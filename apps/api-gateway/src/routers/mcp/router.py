from litestar import Controller, get, post
from src.mcp.protocol import mcp_registry
from pydantic import BaseModel
from typing import Dict, Union, Optional
from sqlalchemy.ext.asyncio import AsyncSession

class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, object]

class MCPController(Controller):
    path = "/api/v1/mcp"

    @get("/tools")
    async def list_tools(self) -> list:
        """Liệt kê danh sách các công cụ mà AI có thể sử dụng (Discovery)"""
        return mcp_registry.tool_metadata

    @post("/call")
    async def call_tool(self, db_session: AsyncSession, data: ToolCallRequest) -> dict:
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
