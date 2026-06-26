import json
import logging
import time
import uuid
import httpx
import asyncio
from typing import List, Dict, Optional, Union
from sqlalchemy import select, func
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
            VoiceProfile.discovered_models,
            VoiceProfile.updated_at
        ).where(VoiceProfile.user_id == user_id)

        result = await db_session.execute(stmt)
        # Elite V2.2: Explicitly typing the scalar result
        data = result.first()

        return AIModelStatusResponse(
            primary_model=data.primary_model if data and data.primary_model else trinity_bridge.primary_model,
            ai_models=data.ai_models if data and data.ai_models else [trinity_bridge.primary_model, trinity_bridge.fallback_model],
            discovered_models=data.discovered_models if data and data.discovered_models else [],
            updated_at=data.updated_at.timestamp() if data and data.updated_at else None
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
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for idx, key in enumerate(all_keys):
                # Use the configured primary model for the ping
                model = trinity_bridge.primary_model
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
        try:
            # 0. Neural Purge (Reset health states to ensure we test everything fresh)
            await AIService.reset_all_keys(preserve_daily=True)
            
            # 1. Discover all available models
            discovered = await trinity_bridge.models_helper.discover_available()
            if not discovered:
                return SuccessResponse(ok=False, message="No models discovered. Check API keys.")

            # 2. Score and sort all discovered models based on Baseline Signals
            scored = []
            for m in discovered:
                if trinity_bridge.models_helper.is_blacklisted(m): continue
                score = trinity_bridge.models_helper._score_model_sync(m)
                scored.append({"name": m, "score": score})
            
            scored.sort(key=lambda x: x["score"], reverse=True)
            
            # 3. Capability Probing Matrix — test candidates until we get a solid waterfall
            winners: list[str] = []
            failed: set[str] = set()
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for s in scored:
                    model = s["name"]
                    if len(winners) >= 6: break # Collect top 6 for better waterfall
                        
                    if await key_rotator.is_model_poisoned(model):
                        failed.add(model); continue

                    try:
                        key = await key_rotator.get_key(model_name=model)
                        if not key: failed.add(model); continue
                    except Exception: failed.add(model); continue
                    
                    # --- LEVEL 1: Connectivity (Ping) ---
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                    try:
                        resp = await client.post(url, json={"contents": [{"parts":[{"text": "ping"}]}]})
                        if resp.status_code != 200:
                            logger.warning(f"[NeuralOpt] Connectivity probe failed for {model}: HTTP {resp.status_code} - {resp.text[:100]}")
                            if resp.status_code == 429 and ("daily" in resp.text.lower() or "quota" in resp.text.lower()):
                                await key_rotator.mark_model_daily(key, model)
                            elif resp.status_code in [400, 404]:
                                await key_rotator.mark_model_poisoned(model, reason=f"HTTP_{resp.status_code}")
                            failed.add(model); continue
                        
                        # Passed Level 1 -> Capability = LEGACY (Baseline)
                        capability = "LEGACY"
                        
                        # --- LEVEL 2: Agentic (Tool Calling Probe) ---
                        # Elite V2.2: Verify if model actually supports function calling
                        tool_probe = {
                            "contents": [{"parts":[{"text": "What time is it? Use get_time tool."}]}],
                            "tools": [{"function_declarations": [{"name": "get_time", "description": "Get current time"}]}],
                            "tool_config": {"function_calling_config": {"mode": "ANY"}}
                        }
                        probe_resp = await client.post(url, json=tool_probe)
                        if probe_resp.status_code == 200:
                            res_json = probe_resp.json()
                            parts = res_json.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                            if any("functionCall" in p for p in parts):
                                capability = "AGENTIC"
                                
                                # --- LEVEL 3: Structural (JSON Compliance) ---
                                json_probe = {
                                    "contents": [{"parts":[{"text": "Return JSON: {'status': 'ok'}"}]}],
                                    "generationConfig": {"response_mime_type": "application/json"}
                                }
                                json_resp = await client.post(url, json=json_probe)
                                if json_resp.status_code == 200:
                                    try:
                                        import json
                                        if json.loads(json_resp.json()["candidates"][0]["content"]["parts"][0]["text"]).get("status") == "ok":
                                            capability = "ELITE"
                                    except: pass
                        
                        # Persist Capability Signal to Redis
                        await key_rotator.mark_model_capability(model, capability)
                        logger.info(f"🏆 [NeuralOpt] Model {model} Qualified as {capability}")
                        
                        if capability in ["AGENTIC", "ELITE"]:
                            winners.append(model)
                        else:
                            # Still healthy but legacy
                            winners.append(model)
                            
                    except Exception as e:
                        logger.warning(f"[NeuralOpt] Probe failed for {model}: {type(e).__name__} - {str(e)}")
                        failed.add(model)
                        
                    await asyncio.sleep(0.8) # RPM Flood Protection (Surgical)

            # 4. Elite V2.2: 100% Dynamic Neural Stack Synthesis (Anti-Hardcode)
            # We construct the waterfall in a fully automated hierarchy:
            # Rank 1-6: Healthy Probed Models (automatically sorted by our Trinity Model Scoring Engine)
            # Bottom: Unprobed or Failed Models as last-resort backups (Max Redundancy)
            final_winners: list[str] = []
            
            # Phase A: Top Healthy Probed Models (dynamically scored)
            for w in winners:
                if w not in final_winners:
                    final_winners.append(w)
            
            # Phase B: Remaining Discovered Models (Unprobed/Failed) at the very bottom
            for s in scored:
                m_name = s["name"]
                if m_name not in final_winners and not trinity_bridge.models_helper.is_blacklisted(m_name):
                    final_winners.append(m_name)
            
            # Limit to top 6 for a deep waterfall
            winners = final_winners[:6]
            
            if not winners:
                winners = [trinity_bridge.primary_model, trinity_bridge.fallback_model]
            
            # Persist to VoiceProfile (Current Scalar Projection Rule)
            from backend.database.models import VoiceProfile
            stmt = select(VoiceProfile).where(VoiceProfile.user_id == user_id)
            profile = (await db_session.execute(stmt)).scalar_one_or_none()
            
            if not profile:
                profile = VoiceProfile(id=str(uuid.uuid4()), user_id=user_id)
                db_session.add(profile)
            
            profile.primary_model = winners[0]
            profile.ai_models = winners[1:6] # FIXED: Ensure correct field name
            profile.updated_at = func.now()
            
            # Explicitly commit for safety in auto-optimize flow
            await db_session.commit()
            
            # Hot-Reload Trinity Bridge
            trinity_bridge.db_primary_model = winners[0]
            trinity_bridge.db_waterfall = winners[1:6]

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
