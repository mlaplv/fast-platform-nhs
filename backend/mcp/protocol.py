import inspect
from typing import Callable, Dict, List
from pydantic import BaseModel, ConfigDict

class MCPTool(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str
    description: str
    parameters: Dict[str, object]

class MCPRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_metadata: List[MCPTool] = []

    def register(self, name: str, description: str):
        def decorator(func: Callable):
            self.tools[name] = func
            # Basic parameter extraction from type hints
            sig = inspect.signature(func)
            parameters = {
                param.name: str(param.annotation) 
                for param in sig.parameters.values() 
                if param.name != "self"
            }
            self.tool_metadata.append(MCPTool(
                name=name,
                description=description,
                parameters=parameters
            ))
            return func
        return decorator

mcp_registry = MCPRegistry()
