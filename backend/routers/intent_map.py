from litestar import Controller, get, post
from backend.services.xohi_memory import xohi_memory
from typing import Dict
import logging

from backend.constants.permissions import PermissionEnum
from backend.guards import PermissionGuard

logger = logging.getLogger("api-gateway")

class IntentMapController(Controller):
    path = "/api/v1/intent/map"
    guards = [PermissionGuard(PermissionEnum.SYS_ADMIN)]

    @get("/")
    async def get_intent_map(self) -> Dict[str, str]:
        """Fetch current Tier 1 dynamic mappings from Redis."""
        try:
            mapping = await xohi_memory.get_system_intent_mapping()
            return mapping or {}
        except Exception as e:
            logger.error(f"[IntentMap] Failed to fetch map: {e}")
            return {}

    @post("/")
    async def update_intent_map(self, data: Dict[str, str]) -> Dict[str, str]:
        """Update or add dynamic intent mappings."""
        try:
            current_map = await xohi_memory.get_system_intent_mapping() or {}
            current_map.update(data)
            await xohi_memory.set_system_intent_mapping(current_map)
            logger.info(f"[IntentMap] Updated mapping with {len(data)} items")
            return current_map
        except Exception as e:
            logger.error(f"[IntentMap] Failed to update map: {e}")
            return {}
