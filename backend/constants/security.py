"""
Elite V2.2: Security Constants.
Centralized location for restricted zones and mutation rules.
"""

# Prefixes that are only accessible from the Admin Domain (*.admin.smartshop.test)
ADMIN_ONLY_PREFIXES: list[str] = [
    "/api/v1/users",
    "/api/v1/settings",
    "/api/v1/notifications",
    "/api/v1/auditor",
    "/api/v1/ai",
    "/api/v1/mcp",
    "/api/v1/scheduler",
    "/api/v1/banner",
    "/api/v1/chat",
    "/api/v1/auth",
    "/api/v1/pulse",
    "/api/v1/intent",
    "/api/v1/voice",
    "/api/v1/content",
    "/api/v1/media",
    "/api/v1/orders",    # Admin order management (Checkout is public via different controller)
    "/ws/stt",           # Voice WebSocket
]

# Shared resources where mutations (POST, PATCH, PUT, DELETE) are restricted to Admin Domain
MUTATION_RESTRICTED_METHODS: list[str] = ["POST", "PATCH", "PUT", "DELETE"]

SHARED_RESOURCE_PREFIXES: list[str] = [
    "/api/v1/products",
    "/api/v1/categories",
    "/api/v1/articles"
]
