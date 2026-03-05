import logging

logger = logging.getLogger("mcp_iam")

class MCPIamGuard:
    """
    R29: Chống The Confused Deputy (MCP Tool Hijacking)
    IAM local cho các agent. Agent bị kiểm soát không thể gọi tool ngoài quyền hạn.
    """
    
    # Define role-based access control (RBAC) lists for MCP Tools
    ROLE_PERMISSIONS = {
        "NanoBot-Tier3": [
            "get_revenue_stats",
            "get_order_summary",
            "list_orders",
            "get_draft_analysis",
            "decrement_stock",
            "search_products_semantic",
        ],
        "NanoBot-Auditor": [
            "create_database_draft",
            "review_database_draft",
            "get_draft_analysis",
        ],
        "NanoBot-Admin": [
            # High privilege agent — includes docker access
            "*" 
        ]
    }

    @classmethod
    def check_permission(cls, agent_role: str, tool_name: str) -> bool:
        """
        Xác minh role của Agent có được phép thực thi Tool này không.
        Returns True nếu hợp lệ, False nếu vi phạm R29.
        """
        allowed_tools = cls.ROLE_PERMISSIONS.get(agent_role, [])
        
        if "*" in allowed_tools:
            return True
            
        if tool_name in allowed_tools:
            return True
            
        logger.error(
            f"[IAM VIOLATION] R29: Agent '{agent_role}' attempted to execute "
            f"unauthorized tool '{tool_name}'. Confused Deputy Attack blocked."
        )
        return False
