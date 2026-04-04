import logging
import hashlib
import json
import os
from typing import List, Optional

logger = logging.getLogger("key-loader")

class KeyLoaderMixin:
    def _parse_keys(self, raw: str | None) -> list[str]:
        if not raw:
            return []
        
        # Elite V2.2: Strip potential shell wrapping quotes
        raw = raw.strip()
        if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
            raw = raw[1:-1].strip()

        try:
            # 1. Try JSON (V2026 Standard)
            decoded = json.loads(raw)
            if isinstance(decoded, list):
                return [str(k).strip() for k in decoded if k]
            return [str(decoded).strip()]
        except:
            # 2. Fallback to comma-separated
            # Strip JSON-like brackets if they exist in the raw string before splitting
            clean_raw = raw.strip("[]")
            return [k.strip().strip('"').strip("'") for k in clean_raw.split(",") if k.strip()]

    async def load_keys(self) -> None:
        """Standardized Key Loading: Merges ENV and DB keys."""
        # Elite 2026: Priority order: Legacy ENV -> Support ENV -> DB
        legacy_keys: list[str] = self._parse_keys(os.getenv("GEMINI_API_KEY"))
        support_keys: list[str] = self._parse_keys(os.getenv("SUPPORT_GEMINI_KEYS"))
        
        db_keys: list[str] = []
        try:
            db_keys = await self._recover_from_db()
        except Exception as e:
            logger.error(f"[KeyLoader] DB Recovery failed: {e}")

        # Unique merge
        all_keys: list[str] = list(dict.fromkeys(legacy_keys + support_keys + db_keys))
        self.keys, self.index = all_keys, 0
        
        if not self.keys:
            logger.warning("[KeyRotator] NO Gemini keys found in ENV or DB!")
        else:
            logger.info(f"[KeyRotator] Successfully loaded {len(self.keys)} Gemini keys.")

    async def _recover_from_db(self) -> list[str]:
        from backend.database.alchemy_config import alchemy_config
        from backend.database.models import VoiceProfile
        from backend.utils.security import GeminiSecurity
        from sqlalchemy import select
        async with alchemy_config.create_session_maker()() as session:
            profiles = (await session.execute(select(VoiceProfile).where(VoiceProfile.gemini_keys_enc != None))).scalars().all()
            recovered = [k for p in profiles for k in (GeminiSecurity.decrypt(p.gemini_keys_enc) or [])]
            return list(set(recovered))

    def _get_key_id(self, key: Optional[str]) -> str:
        if not key: return "no_key"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    async def save_discovered_models(self, models: list[str]):
        if not self._use_redis or not self.client: return
        try: await self.client.set(self.DISCOVERED_MODELS_KEY, json.dumps(models), ex=self.MAX_COOLDOWN)
        except: pass

    async def get_discovered_models(self) -> list[str]:
        if not self._use_redis or not self.client: return []
        try:
            val = await self.client.get(self.DISCOVERED_MODELS_KEY)
            return json.loads(val) if val else []
        except: return []

    def get_count(self) -> int: return len(self.keys)
    def get_next_key(self) -> str:
        if not self.keys: return ""
        k = self.keys[self.index]; self.index = (self.index + 1) % len(self.keys); return k
