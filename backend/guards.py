from typing import List, Union, Callable
from litestar.connection import ASGIConnection
from litestar.handlers.base import BaseRouteHandler
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException

def PermissionGuard(permissions: Union[str, List[str]]) -> Callable:
    """
    Elite Permission Guard for Litestar.
    Checks if the user has the required granular permissions stored in JWT claims.
    """
    if isinstance(permissions, str):
        required_perms = [permissions]
    else:
        required_perms = permissions

    def guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
        user = connection.scope.get("state", {}).get("user")
        
        if not user:
            raise NotAuthorizedException("Session Expired or Identity Not Found")

        user_perms = user.get("perms", [])
        user_roles = user.get("roles", [])

        # SUPER_ADMIN always has access
        if "SUPER_ADMIN" in user_roles:
            return

        # Check if user has ALL required permissions
        if all(perm in user_perms for perm in required_perms):
            return

        raise PermissionDeniedException("Security Clearance Level Insufficient")

    return guard
