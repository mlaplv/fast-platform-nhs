from typing import List, Union, Callable
from litestar.connection import ASGIConnection
from litestar.handlers.base import BaseRouteHandler
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from backend.constants.permissions import PermissionEnum

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

    def guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        user = connection.scope.get("state", {}).get("user")
        
        if not user:
            raise NotAuthorizedException("Session Expired or Identity Not Found")

        from backend.services.policy_evaluator import PolicyEvaluator, PolicyContext
        
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
