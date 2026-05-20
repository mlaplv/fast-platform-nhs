import logging
from typing import Dict, Optional
from litestar.exceptions import PermissionDeniedException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.system import Draft
import json
import uuid

logger = logging.getLogger("api-gateway")

class FourEyesPrincipleManager:
    """
    Elite V2.2: Four-Eyes Principle DB Operation Manager.
    Enforces dual approval ('4-Eyes Principle') for critical operations.
    """
    
    CRITICAL_TABLES = ["users", "roles", "permissions", "system_settings", "products"]

    @staticmethod
    async def intercept_critical_action(
        session: AsyncSession,
        actor_id: str,
        action: str,
        target_table: str,
        target_id: Optional[str],
        payload: Dict[str, object],
        is_super_admin: bool = False
    ) -> bool:
        """
        Intercepts critical actions. 
        If not Super Admin, converts the action into a PENDING Draft.
        Returns True if the action is intercepted (should NOT continue), False otherwise.
        """
        
        # Super Admin has 'Direct Execution' power (unless System is locked down)
        if is_super_admin:
            return False

        if target_table in FourEyesPrincipleManager.CRITICAL_TABLES or action == "DELETE":
            logger.warning(f"🎖️ [FOUR_EYES_PRINCIPLE] Intercepted {action} on {target_table} by {actor_id}. Redirecting to Draft.")
            
            new_draft = Draft(
                id=str(uuid.uuid4()),
                proposed_by=actor_id,
                target_model=target_table,
                target_id=target_id,
                action=action,
                payload=payload,
                status="PENDING"
            )
            session.add(new_draft)
            return True
            
        return False

four_eyes_manager = FourEyesPrincipleManager()
