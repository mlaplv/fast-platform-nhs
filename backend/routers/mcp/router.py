from __future__ import annotations
from litestar import Controller, get, post
from backend.mcp.protocol import mcp_registry
from pydantic import BaseModel, ConfigDict
from typing import Dict, Union, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.guards import PermissionGuard
from backend.constants.permissions import PermissionEnum

class ToolCallRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str
    arguments: Dict[str, object]

class MCPController(Controller):
    path = "/api/v1/mcp"
    guards = [PermissionGuard(PermissionEnum.SYS_ADMIN)]

    @get("/tools")
    async def list_tools(self) -> List[Dict[str, object]]:
        """Liệt kê danh sách các công cụ mà AI có thể sử dụng (Discovery)"""
        return mcp_registry.tool_metadata

    @post("/call")
    async def call_tool(self, db_session: "AsyncSession", data: ToolCallRequest) -> Dict[str, object]:
        """Thực thi một công cụ cụ thể dựa trên yêu cầu từ AI"""
        if data.name not in mcp_registry.tools:
            return {"status": "error", "message": f"Tool '{data.name}' not found."}
        
        tool_func = mcp_registry.tools[data.name]
        try:
            # Inject session into the tool function
            result = await tool_func(db_session=db_session, **data.arguments)
            return {"status": "success", "data": result}
        except Exception as e:
            import logging
            logging.getLogger("api-gateway").error(f"[MCP] Tool execution error ({data.name}): {e}")
            return {"status": "error", "message": str(e)}
