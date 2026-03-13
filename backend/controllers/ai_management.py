import logging
import time
import uuid
from typing import List, Dict, Optional
from litestar import Controller, get, post, Request
from litestar.exceptions import NotAuthorizedException
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
    last_used: float
    status: str

class BulkKeyInput(BaseModel):
    keys: str

class ModelConfig(BaseModel):
    primary_model: Optional[str] = None
    ai_models: List[str] = []

class AIController(Controller):
    """
    [ADMIN ONLY] AI Engine Configuration & Monitoring.
    
    MANAGEMENT RULES (IMPORTANT FOR FUTURE):
    1. RESET: The 'Reset All Keys' button clears all 429/Cooldown states in Redis 
       AND triggers an immediate hot-reload from the Database + ENV.
    2. BULK UPLOAD: The Save button uses 'REPLACE' logic. 
       Whatever you type in the box becomes the NEW pool. It does NOT append.
    3. HOT-RELOAD: Changes made here reflect instantly in TrinityBridge via key_rotator.load_keys().
    """
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

    @post("/keys/reset")
    async def reset_all_keys(self) -> Dict[str, object]:
        """Reset ALL key health states (clear blacklist + cooldowns). Safe to call anytime."""
        if not key_rotator._use_redis or not key_rotator.client:
            return {"status": "error", "message": "Redis unavailable"}

        try:
            cleared = await key_rotator.reset_health()
            logger.info(f"[AIController] Key pool reset complete. {cleared} Redis records cleared.")
            return {"status": "success", "cleared": cleared, "message": f"Đã reset hệ thống Key về trạng thái sạch (Clean State) và nạp lại từ DB."}
        except Exception as e:
            logger.exception(f"[AIController] Reset failed: {e}")
            return {"status": "error", "message": str(e)}

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
            
            # V75: Fix - Find or create profile and save keys
            stmt = select(VoiceProfile).where(VoiceProfile.user_id == user_info["id"])
            result = await voice_repo.session.execute(stmt)
            profile = result.scalar_one_or_none()
            
            if not profile:
                profile = VoiceProfile(id=str(uuid.uuid4()), user_id=user_info["id"])
                await voice_repo.add(profile)
            
            profile.gemini_keys_enc = encrypted_blob
            
            logger.info("[AIController] Committing transaction...")
            await voice_repo.session.commit()
            
            # 3. Reload everything into memory
            await key_rotator.load_keys()
            logger.info("[AIController] DB Commit and Key Reload successful")
            
            return {
                "status": "success", 
                "count": len(new_keys),
                "message": f"Successfully updated {len(new_keys)} keys."
            }
        except Exception as e:
            logger.exception(f"[AIController] Bulk sync failed: {e}")
            return {"status": "error", "message": str(e)}

    @get("/models/discover")
    async def discover_models(self, request: Request, voice_repo: VoiceProfileRepository) -> Dict[str, object]:
        """Fetch available Gemini models directly from Google API and persist to DB."""
        import httpx
        
        user_info = getattr(request.state, "user", None)
        if not user_info:
             raise Exception("User session required")

        try:
            # 1. Get an active key
            key = await key_rotator.get_key()
            models = []
            
            if key:
                # 2. Fetch from Google Discovery API
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        for m in data.get("models", []):
                            name = m.get("name", "").replace("models/", "")
                            methods = m.get("supportedGenerationMethods", [])
                            if "generateContent" in methods and "gemini" in name:
                                models.append(name)
                        models.sort()

            # 3. Persist to DB for this user profile (only if we found models)
            if models:
                stmt = select(VoiceProfile).where(VoiceProfile.user_id == user_info["id"])
                result = await voice_repo.session.execute(stmt)
                profile = result.scalar_one_or_none()
                
                if not profile:
                    profile = VoiceProfile(id=str(uuid.uuid4()), user_id=user_info["id"])
                    await voice_repo.add(profile)
                
                profile.discovered_models = models
                await voice_repo.session.commit()
            
            return {
                "status": "success",
                "models": models
            }
        except Exception as e:
            logger.error(f"[AIController] Discovery/Persist failed: {e}")
            return {"status": "error", "message": str(e)}

    @get("/models")
    async def get_ai_models(self, request: Request, voice_repo: VoiceProfileRepository) -> Dict[str, object]:
        """Returns the current model waterfall configuration AND discovered suggestions."""
        user_info = getattr(request.state, "user", None)
        if not user_info:
             raise Exception("User session required")
             
        stmt = select(VoiceProfile).where(VoiceProfile.user_id == user_info["id"])
        result = await voice_repo.session.execute(stmt)
        profile = result.scalar_one_or_none()
        
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
        
        return {
            "primary_model": profile.primary_model if profile else trinity_bridge.default_model_name,
            "ai_models": profile.ai_models if profile else trinity_bridge.model_waterfall,
            "discovered_models": profile.discovered_models if profile else []
        }

    @post("/models")
    async def update_ai_models(self, request: Request, voice_repo: VoiceProfileRepository, data: ModelConfig) -> Dict[str, str]:
        """Update the AI model waterfall configuration."""
        user_info = getattr(request.state, "user", None)
        if not user_info:
             raise Exception("User session required")
             
        stmt = select(VoiceProfile).where(VoiceProfile.user_id == user_info["id"])
        result = await voice_repo.session.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            profile = VoiceProfile(id=str(uuid.uuid4()), user_id=user_info["id"])
            await voice_repo.add(profile)
            
        profile.primary_model = data.primary_model
        profile.ai_models = data.ai_models
        
        await voice_repo.session.commit()
        
        # V75.11: Hyper-Fast Hot-Reload (Direct Inject)
        from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
        trinity_bridge.db_primary_model = data.primary_model
        trinity_bridge.db_waterfall = data.ai_models
        logger.info(f"[AIController] TrinityBridge hot-reloaded via Direct Inject.")
        
        return {"status": "success", "message": "Model configuration updated and hot-reloaded."}

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
