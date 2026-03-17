import json
import logging
import time
from typing import Optional, Dict, Any, TypedDict

from backend.services.xohi_memory import xohi_memory

logger = logging.getLogger("api-gateway")

# Synapse TTL: 90 seconds (short-term memory for confirmations)
SYNAPSE_TTL = 90

class IntentSynapseService:
    """
    Neural Synapse Service — Handles Recurrent Intent Propagation (RIP).
    Stores pending intents during clarification turns to be 're-activated' by confirmations.
    """

    class IntentPayload(TypedDict):
        query: str
        classification: Dict[str, Any]  # IntentResponse data dictionary
        timestamp: float

    @staticmethod
    async def store_pending_intent(user_id: str, classification_data: Dict[str, Any], query: str) -> None:

        """
        Stores a 'floating' intent that awaits confirmation.
        """
        key = f"xohi:synapse:{user_id}"
        payload = {
            "query": query,
            "classification": classification_data,
            "timestamp": time.time()
        }
        try:
            if xohi_memory._use_redis:
                await xohi_memory.client.set(key, json.dumps(payload, ensure_ascii=False), ex=SYNAPSE_TTL)
            else:
                xohi_memory._fallback_cache[f"synapse:{user_id}"] = payload
            logger.info(f"[IntentSynapse] Stored pending intent for {user_id}: '{query}'")
        except Exception as e:
            logger.error(f"[IntentSynapse] Failed to store synapse: {e}")

    @staticmethod
    async def retrieve_and_clear(user_id: str) -> Optional[IntentPayload]:

        """
        Retrieves the pending intent and clears it (Atomic Consumption).
        """
        key = f"xohi:synapse:{user_id}"
        try:
            if xohi_memory._use_redis:
                data = await xohi_memory.client.get(key)
                if data:
                    await xohi_memory.client.delete(key)
                    return json.loads(data)
            else:
                data = xohi_memory._fallback_cache.pop(f"synapse:{user_id}", None)
                return data
        except Exception as e:
            logger.error(f"[IntentSynapse] Retrieval failed: {e}")
        return None

intent_synapse = IntentSynapseService()
