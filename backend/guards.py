from typing import List, Union, Callable
from litestar.connection import ASGIConnection
from litestar.handlers.base import BaseRouteHandler
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from backend.constants.permissions import PermissionEnum
from backend.database import async_session_maker
from backend.database.models import User
from sqlalchemy import select
from backend.services.policy_evaluator import PolicyEvaluator, PolicyContext

def PermissionGuard(permissions: Union[PermissionEnum, str, List[Union[PermissionEnum, str]]]) -> Callable:
    """
    Elite Permission Guard PBAC for Litestar.
    Checks if the user has the required granular permissions stored in JWT claims
    using PolicyEvaluator for Context-Aware evaluation.
    """
    if not isinstance(permissions, list):
        # Convert Enum members to their string values
        from enum import Enum
        required_perms = [str(permissions.value) if isinstance(permissions, Enum) else str(permissions)]
    else:
        from enum import Enum
        required_perms = [str(p.value) if isinstance(p, Enum) else str(p) for p in permissions]

    async def guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        user = connection.scope.get("state", {}).get("user")
        
        if not user:
            raise NotAuthorizedException("Session Expired or Identity Not Found")

        # [Elite V3] Stateless Revocation Check (Chỉ áp dụng cho Write/Mutation)
        if connection.method in ("POST", "PUT", "PATCH", "DELETE"):
            token_stamp = user.get("stamp")
            user_id = user.get("id")
            
            if not token_stamp or token_stamp == "MISSING" or not user_id:
                raise NotAuthorizedException("Legacy token detected. Please login again to obtain a V3 Security Stamp.")

            async with async_session_maker() as session:
                stmt = select(User.security_stamp).where(User.id == user_id)
                result = await session.execute(stmt)
                db_stamp = result.scalar_one_or_none()
                if not db_stamp or db_stamp != token_stamp:
                    raise NotAuthorizedException("Security stamp revoked or invalid. Please login again.")

        # Build Context từ kết nối ASGI
        headers = dict(connection.headers)
        domain = headers.get("host", headers.get("x-forwarded-host", ""))
        
        context = PolicyContext(
            user_roles=tuple(user.get("roles", [])),
            user_perms=tuple(user.get("perms", [])),
            required_perms=tuple(required_perms),
            action=f"{connection.method} {connection.url.path}",
            domain=domain,
        )
        
        # PBAC Evaluation Siêu tốc
        result = PolicyEvaluator.evaluate(context)
        if not result.allowed:
            raise PermissionDeniedException(f"Security Clearance Level Insufficient: {result.reason}")

    return guard
