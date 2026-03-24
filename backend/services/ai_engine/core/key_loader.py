import logging
import hashlib
import json
import os
from typing import List, Optional

logger = logging.getLogger("key-loader")

class KeyLoaderMixin:
    async def load_keys(self):
        """Standardized Key Loading: Merges ENV and DB keys."""
        env_keys = [k.strip() for k in os.getenv("GEMINI_API_KEY", "").split(",") if k.strip()]
        db_keys = []
        try: db_keys = await self._recover_from_db()
        except: pass
        self.keys, self.index = list(dict.fromkeys(env_keys + db_keys)), 0
        if not self.keys: logger.warning("[KeyRotator] NO Gemini keys found in ENV or DB!")

    async def _recover_from_db(self) -> List[str]:
        from backend.database.alchemy_config import alchemy_config
        from backend.database.models import VoiceProfile
        from backend.utils.security import GeminiSecurity
        from sqlalchemy import select
        async with alchemy_config.create_session_maker()() as session:
            profiles = (await session.execute(select(VoiceProfile).where(VoiceProfile.gemini_keys_enc != None))).scalars().all()
            recovered = [k for p in profiles for k in GeminiSecurity.decrypt_keys(p.gemini_keys_enc)]
            return list(set(recovered))

    def _get_key_id(self, key: Optional[str]) -> str:
        if not key: return "no_key"
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    async def save_discovered_models(self, models: List[str]):
        if not self._use_redis or not self.client: return
        try: await self.client.set(self.DISCOVERED_MODELS_KEY, json.dumps(models), ex=self.MAX_COOLDOWN)
        except: pass

    async def get_discovered_models(self) -> List[str]:
        if not self._use_redis or not self.client: return []
        try:
            val = await self.client.get(self.DISCOVERED_MODELS_KEY)
            return json.loads(val) if val else []
        except: return []

    def get_count(self) -> int: return len(self.keys)
    def get_next_key(self) -> str:
        if not self.keys: return ""
        k = self.keys[self.index]; self.index = (self.index + 1) % len(self.keys); return k
