import logging
import time
import uuid
from typing import List, Dict
from litestar import Controller, get, post, Request
from litestar.di import Provide
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.utils.security import GeminiSecurity
from backend.database.models import User, VoiceProfile
from backend.database.repositories import UserRepository, VoiceProfileRepository, provide_user_repo, provide_voice_repo
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logger = logging.getLogger("api-gateway")

class KeyStats(BaseModel):
    index: int
    key_preview: str
    fail_count: int
    health_score: int
    status: str
    last_used: float

class BulkKeyInput(BaseModel):
    keys: str

class AIController(Controller):
    path = "/api/v1/admin/ai"
    dependencies = {
        "user_repo": Provide(provide_user_repo),
        "voice_repo": Provide(provide_voice_repo),
    }
    tags = ["AI Management"]

    @get("/keys")
    async def get_all_key_stats(self) -> List[KeyStats]:
        """Returns real-time metrics for all Gemini keys."""
        all_keys = key_rotator.keys
        stats = []
        now = time.time()
        
        for idx, key in enumerate(all_keys):
            # V70.1: Use Hash ID for persistent tracking
            kid = key_rotator._get_key_id(key)
            meta = await key_rotator.client.hgetall(f"{key_rotator.METADATA_PREFIX}{kid}")
            is_blacklisted = await key_rotator.client.exists(f"{key_rotator.BLACKLIST_PREFIX}{kid}")
            
            fail_count = int(meta.get("fail_count", 0))
            last_used = float(meta.get("last_used", 0))
            
            status = "ACTIVE"
            if is_blacklisted:
                status = "DEAD"
            elif fail_count > 0:
                cooldown = min(key_rotator.BASE_COOLDOWN * (2 ** (fail_count - 1)), key_rotator.MAX_COOLDOWN)
                if now - last_used < cooldown:
                    status = "COOLDOWN"

            stats.append(KeyStats(
                index=idx,
                key_preview=f"{key[:8]}...{key[-4:]}",
                fail_count=fail_count,
                health_score=int(meta.get("health_score", 100)),
                status=status,
                last_used=last_used
            ))
        return stats

    @post("/keys/bulk")
    async def sync_bulk_keys(self, request: Request, user_repo: UserRepository, voice_repo: VoiceProfileRepository, data: BulkKeyInput) -> Dict[str, object]:
        """Bulk upload and save Gemini keys."""
        logger.info(f"[AIController] Received bulk sync request (keys: {len(data.keys)} chars)")
        
        new_keys = [k.strip() for k in data.keys.replace(",", "\n").split("\n") if k.strip()]
        if not new_keys:
             logger.warning("[AIController] No valid keys found in input")
             return {"status": "error", "message": "No valid keys found"}

        user_info = getattr(request.state, "user", None)
        if not user_info:
             logger.warning("[AIController] No user info in request state")
             raise NotAuthorizedException("User session required")
        
        try:
            logger.info(f"[AIController] Encrypting {len(new_keys)} keys...")
            encrypted_blob = GeminiSecurity.encrypt_keys(new_keys)
            
            # 1. Update In-Memory Rotator (Hot)
            logger.info("[AIController] Updating hot rotator...")
            key_rotator.set_keys(new_keys)
            
            # 2. Persist to DB
            logger.info(f"[AIController] Persisting to DB for user: {user_info.get('sub')}")
            # The following imports are already at the top of the file, but kept here as per instruction
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            from backend.database.models import User, VoiceProfile

            stmt = select(User).where(User.email == user_info["sub"]).options(selectinload(User.voice_profile))
            result = await user_repo.session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.error(f"[AIController] User {user_info.get('sub')} not found in DB during sync")
                return {"status": "error", "message": "User context unavailable"}

            if user.voice_profile:
                logger.info("[AIController] Updating existing voice profile...")
                user.voice_profile.gemini_keys_enc = encrypted_blob
            else:
                logger.info("[AIController] Creating new voice profile...")
                new_profile = VoiceProfile(
                    id=str(uuid.uuid4()),
                    user_id=str(user.id),
                    gemini_keys_enc=encrypted_blob
                )
                user_repo.session.add(new_profile)
            
            logger.info("[AIController] Committing transaction...")
            await user_repo.session.commit()
            logger.info("[AIController] DB Commit successful")
            
            return {
                "status": "success", 
                "count": len(new_keys),
                "message": f"Successfully updated {len(new_keys)} keys."
            }
        except Exception as e:
            logger.exception(f"[AIController] Error during bulk sync: {e}")
            return {"status": "error", "message": str(e)}
    @post("/test/{index:int}")
    async def test_key(self, index: int) -> Dict[str, str]:
        """Manually trigger a health check for a specific key."""
        if index < 0 or index >= len(key_rotator.keys):
            return {"status": "error", "message": "Invalid index"}
            
        key = key_rotator.keys[index]
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
                resp = await client.post(url, json={"contents": [{"parts":[{"text": "ping"}]}]})
                
                if resp.status_code == 200:
                    await key_rotator.set_success(key)
                    return {"status": "success", "message": "Key is healthy"}
                else:
                    await key_rotator.mark_unhealthy(key, reason=f"HTTP_{resp.status_code}")
                    return {"status": "error", "message": f"Ping failed with status {resp.status_code}"}
        except Exception as e:
            await key_rotator.mark_unhealthy(key, reason=str(e))
            return {"status": "error", "message": str(e)}
