import json
import logging
import time
import uuid
import httpx
import asyncio
from typing import List, Dict, Optional, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from litestar.exceptions import HTTPException

from backend.schemas.common import SuccessResponse, UserID
from backend.schemas.ai import KeyStats, BulkKeyInput, ModelConfig, ModelDiscoveryResponse, AIModelStatusResponse
from backend.database.models import VoiceProfile
from backend.services.ai_engine.core.key_rotator import key_rotator
from backend.services.ai_engine.core.trinity_bridge import trinity_bridge
from backend.utils.security import GeminiSecurity

logger = logging.getLogger("api-gateway")

class AIService:
    @staticmethod
    async def get_all_key_stats() -> List[KeyStats]:
        """Returns real-time metrics for all Gemini keys."""
        all_keys = key_rotator.keys
        stats = []
        now = time.time()

        for idx, key in enumerate(all_keys):
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

    @staticmethod
    async def reset_all_keys(preserve_daily: bool = False) -> SuccessResponse:
        """Reset ALL key health states."""
        if not key_rotator._use_redis or not key_rotator.client:
            return SuccessResponse(ok=False, message="Redis unavailable")

        try:
            cleared = await key_rotator.reset_health(preserve_daily=preserve_daily)
            logger.info(f"[AIService] Key pool reset complete. {cleared} Redis records cleared.")
            return SuccessResponse(
                ok=True,
                data={"cleared": cleared},
                message=f"Đã reset hệ thống Key về trạng thái sạch (Clean State) và nạp lại từ DB."
            )
        except Exception as e:
            logger.exception(f"[AIService] Reset failed: {e}")
            return SuccessResponse(ok=False, message=str(e))

    @staticmethod
    async def sync_bulk_keys(db_session: AsyncSession, user_id: UserID, data: BulkKeyInput) -> SuccessResponse:
        """Bulk upload and save Gemini keys."""
        raw_input: str = data.keys.strip()
        new_keys: list[str] = []

        try:
            # 1. Try JSON (Sếp copy từ .env)
            decoded = json.loads(raw_input)
            if isinstance(decoded, list):
                new_keys = [str(k).strip() for k in decoded if k]
            else:
                new_keys = [str(decoded).strip()]
        except json.JSONDecodeError:
            # 2. Fallback to Legacy CSV/Newline
            new_keys = [k.strip() for k in raw_input.replace(",", "\n").split("\n") if k.strip()]

        if not new_keys:
             return SuccessResponse(ok=False, message="No valid keys detected in pool.")

        try:
            encrypted_blob = GeminiSecurity.encrypt(new_keys)

            stmt = select(VoiceProfile).where(VoiceProfile.user_id == user_id)
            result = await db_session.execute(stmt)
            profile = result.scalar_one_or_none()

            if not profile:
                profile = VoiceProfile(id=str(uuid.uuid4()), user_id=user_id)
                db_session.add(profile)

            profile.gemini_keys_enc = encrypted_blob
            await db_session.flush() # Ensure it's in DB before reload

            # Reload into memory
            await key_rotator.load_keys()
            return SuccessResponse(
                ok=True,
                id=str(profile.id),
                data={"count": len(new_keys)},
                message=f"Successfully updated {len(new_keys)} keys."
            )
        except Exception as e:
            logger.exception(f"[AIService] Bulk sync failed: {e}")
            return SuccessResponse(ok=False, message=str(e))

    @staticmethod
    async def discover_models(db_session: AsyncSession, user_id: UserID) -> ModelDiscoveryResponse:
        """Fetch available Gemini models and persist (Using Centralized Discovery)."""
        try:
            # V76: Use the helper to ensure Blacklist/Gemma filtering
            models = await trinity_bridge.models_helper.discover_available()

            if models:
                stmt = select(VoiceProfile).where(VoiceProfile.user_id == user_id)
                result = await db_session.execute(stmt)
                profile = result.scalar_one_or_none()

                if not profile:
                    profile = VoiceProfile(id=str(uuid.uuid4()), user_id=user_id)
                    db_session.add(profile)

                profile.discovered_models = models

            return ModelDiscoveryResponse(status="success", models=models)
        except Exception as e:
            logger.error(f"[AIService] Discovery/Persist failed: {e}")
            return ModelDiscoveryResponse(status="error", models=[])

    @staticmethod
    async def get_ai_models(db_session: AsyncSession, user_id: UserID) -> AIModelStatusResponse:
        """Returns the current model waterfall (Scalar Projection Rule 1.5)."""
        stmt = select(
            VoiceProfile.primary_model,
            VoiceProfile.ai_models,
            VoiceProfile.discovered_models
        ).where(VoiceProfile.user_id == user_id)

        result = await db_session.execute(stmt)
        # Elite V2.2: Explicitly typing the scalar result
        data = result.first()

        return AIModelStatusResponse(
            primary_model=data.primary_model if data and data.primary_model else trinity_bridge.primary_model,
            ai_models=data.ai_models if data and data.ai_models else [trinity_bridge.primary_model, trinity_bridge.fallback_model],
            discovered_models=data.discovered_models if data and data.discovered_models else []
        )

    @staticmethod
    async def update_ai_models(db_session: AsyncSession, user_id: UserID, data: ModelConfig) -> SuccessResponse:
        """Update the AI model waterfall configuration."""
        stmt = select(VoiceProfile).where(VoiceProfile.user_id == user_id)
        result = await db_session.execute(stmt)
        profile = result.scalar_one_or_none()

        if not profile:
            profile = VoiceProfile(id=str(uuid.uuid4()), user_id=user_id)
            db_session.add(profile)

        profile.primary_model = data.primary_model
        profile.ai_models = data.ai_models

        # V75.11: Hyper-Fast Hot-Reload (Direct Inject)
        trinity_bridge.db_primary_model = data.primary_model
        trinity_bridge.db_waterfall = data.ai_models

        return SuccessResponse(ok=True, id=str(profile.id), message="Model configuration updated and hot-reloaded.")

    @staticmethod
    async def test_key(index: int) -> SuccessResponse:
        """Manually trigger a health check for a specific key."""
        if index < 0 or index >= len(key_rotator.keys):
            return SuccessResponse(ok=False, message="Invalid index")

        key = key_rotator.keys[index]
        try:
            async with httpx.AsyncClient() as client:
                m = trinity_bridge.models_helper.default_model
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
                resp = await client.post(url, json={"contents": [{"parts":[{"text": "ping"}]}]})

                if resp.status_code == 200:
                    await key_rotator.set_success(key)
                    return SuccessResponse(ok=True, message="Key is healthy")
                else:
                    await key_rotator.mark_unhealthy(key, reason=f"HTTP_{resp.status_code}")
                    return SuccessResponse(ok=False, message=f"Ping failed with status {resp.status_code}")
        except Exception as e:
            await key_rotator.mark_unhealthy(key, reason=str(e))
            return SuccessResponse(ok=False, message=str(e))

    @staticmethod
    async def deep_check_all_keys() -> SuccessResponse:
        """
        [Elite V2.2] Perform a comprehensive 'ping' test on all keys for real-time quota verification.
        """
        all_keys = key_rotator.keys
        results = []
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for idx, key in enumerate(all_keys):
                # We use gemini-1.5-flash for the ping as it's the most available
                model = "gemini-1.5-flash"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                
                try:
                    resp = await client.post(url, json={"contents": [{"parts":[{"text": "ping"}]}]})
                    if resp.status_code == 200:
                        await key_rotator.set_success(key)
                        results.append({"index": idx, "status": "HEALTHY", "code": 200})
                    elif resp.status_code == 429:
                        # 429 means Quota Exhausted
                        await key_rotator.mark_unhealthy(key, reason="QUOTA_EXHAUSTED")
                        results.append({"index": idx, "status": "EXHAUSTED", "code": 429})
                    else:
                        await key_rotator.mark_unhealthy(key, reason=f"HTTP_{resp.status_code}")
                        results.append({"index": idx, "status": "FAILED", "code": resp.status_code})
                except Exception as e:
                    await key_rotator.mark_unhealthy(key, reason=str(e))
                    results.append({"index": idx, "status": "ERROR", "message": str(e)})

        # Record the deep check timestamp in Redis
        if key_rotator.client:
            await key_rotator.client.set("system:ai:last_deep_check", str(time.time()))

        return SuccessResponse(
            ok=True, 
            data=results, 
            message=f"Deep Scan Complete. Scanned {len(all_keys)} keys."
        )

    @staticmethod
    async def get_orchestration_config() -> Dict:
        """Fetch global orchestration config from SystemSettings."""
        from backend.database.alchemy_config import alchemy_config
        from backend.database.models import SystemSetting
        from backend.services.ai_engine.core.trinity_models import DEFAULT_AI_CONFIG
        
        async with alchemy_config.create_session_maker()() as session:
            setting = (await session.execute(
                select(SystemSetting).where(SystemSetting.key == "ai_orchestration_config")
            )).scalar_one_or_none()
            return setting.value if setting else DEFAULT_AI_CONFIG

    @staticmethod
    async def update_orchestration_config(db_session: AsyncSession, data: Dict) -> SuccessResponse:
        """Update global orchestration config in SystemSettings."""
        from backend.database.models import SystemSetting
        
        setting = (await db_session.execute(
            select(SystemSetting).where(SystemSetting.key == "ai_orchestration_config")
        )).scalar_one_or_none()
        
        if not setting:
            setting = SystemSetting(key="ai_orchestration_config")
            db_session.add(setting)
            
        setting.value = data
        await db_session.flush()
        
        # Elite Hot-Reload: Clear TTL cache in trinity_models
        trinity_bridge.models_helper._last_config_load = 0
        
        return SuccessResponse(ok=True, message="Global AI Orchestration config updated and hot-reloaded.")

    @staticmethod
    async def auto_optimize_stack(db_session: AsyncSession, user_id: UserID) -> SuccessResponse:
        """
        [Elite V2.2] Automatically identifies the top 5 healthiest models and persists them to DB.
        Tests ALL discovered models and ranks them by health + capability score.
        """
        from backend.services.ai_engine.core.trinity_models import HARD_BLACKLIST
        
        try:
            # 0. Neural Purge (Reset health states to ensure we test everything fresh)
            await AIService.reset_all_keys(preserve_daily=True)
            
            # 1. Discover all available models (already filtered by HARD_BLACKLIST in discover_available)
            discovered = await trinity_bridge.models_helper.discover_available()
            if not discovered:
                return SuccessResponse(ok=False, message="No models discovered. Check API keys.")

            # 2. Score and sort all discovered models
            scored = []
            for m in discovered:
                score = trinity_bridge.models_helper._score_model(m)
                # Double-safety: skip anything that slipped past with negative score
                if score < 0:
                    continue
                scored.append({"name": m, "score": score})
            
            scored.sort(key=lambda x: x["score"], reverse=True)
            
            # 3. Health Test — test ALL scored candidates until we get 5 healthy ones
            winners: list[str] = []
            failed: set[str] = set()
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                for s in scored:
                    model = s["name"]
                    if len(winners) >= 5:
                        break
                        
                    # Elite V2.2: Skip models already known as poisoned
                    if await key_rotator.is_model_poisoned(model):
                        failed.add(model)
                        continue

                    try:
                        key = await key_rotator.get_key(model_name=model)
                        if not key:
                            failed.add(model)
                            continue
                    except Exception:
                        failed.add(model)
                        continue
                    
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                    try:
                        resp = await client.post(url, json={"contents": [{"parts":[{"text": "ping"}]}]})
                        if resp.status_code == 200:
                            winners.append(model)
                        elif resp.status_code == 429:
                            if "daily" in resp.text.lower() or "quota" in resp.text.lower():
                                await key_rotator.mark_model_daily(key, model)
                            failed.add(model)
                        elif resp.status_code in [400, 404]:
                            await key_rotator.mark_model_poisoned(model, reason=f"HTTP_{resp.status_code}")
                            failed.add(model)
                        else:
                            failed.add(model)
                    except Exception:
                        failed.add(model)
                        
                    # Elite V2.2: RPM Flood Protection
                    await asyncio.sleep(0.3)

            # 4. Fill remaining slots with untested models (sorted by score, skip failed ones)
            if len(winners) < 5:
                for s in scored:
                    if s["name"] not in winners and s["name"] not in failed:
                        winners.append(s["name"])
                        if len(winners) >= 5:
                            break

            # 5. Final Safety: Remove any blacklisted model that might have slipped through
            winners = [w for w in winners if not any(hbl in w.lower() for hbl in HARD_BLACKLIST)]

            if not winners:
                # Absolute Fallback (only known-good, non-blacklisted models)
                winners = [
                    trinity_bridge.primary_model,
                    "gemini-2.5-flash",
                    "gemini-1.5-flash", 
                    "gemini-1.5-pro",
                    "gemini-2.0-flash",
                ]

            # 6. Persist to DB
            from backend.database.models import VoiceProfile
            stmt = select(VoiceProfile).where(VoiceProfile.user_id == user_id)
            result = await db_session.execute(stmt)
            profile = result.scalar_one_or_none()

            if not profile:
                profile = VoiceProfile(id=str(uuid.uuid4()), user_id=user_id)
                db_session.add(profile)

            profile.primary_model = winners[0]
            profile.ai_models = winners[1:]
            
            # Hot-Reload Trinity Bridge
            trinity_bridge.db_primary_model = winners[0]
            trinity_bridge.db_waterfall = winners[1:]

            logger.info(f"[AIService] Auto-Optimize complete: {winners} (tested {len(scored)}, healthy {len(winners)}, failed {len(failed)})")

            return SuccessResponse(
                ok=True, 
                data={"top_5": winners, "tested": len(scored), "failed": len(failed)}, 
                message=f"Neural Stack Optimized: Lead={winners[0]}, Backups={', '.join(winners[1:])}"
            )
        except Exception as e:
            logger.exception(f"[AIService] Auto-optimize failed: {e}")
            return SuccessResponse(ok=False, message=str(e))

ai_service = AIService()
