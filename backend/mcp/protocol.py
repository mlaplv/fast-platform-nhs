import inspect
from typing import Callable, Dict, List, TypeVar

T = TypeVar("T", bound=Callable)

from pydantic import BaseModel, ConfigDict

class MCPTool(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str
    description: str
    parameters: Dict[str, str]

class MCPRegistry:
    def __init__(self) -> None:
        self.tools: Dict[str, Callable] = {}
        self.tool_metadata: List[MCPTool] = []

    def register(self, name: str, description: str) -> Callable[[T], T]:
        def decorator(func: T) -> T:
            self.tools[name] = func
            # Basic parameter extraction from type hints
            sig = inspect.signature(func)
            parameters: Dict[str, str] = {
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

mcp_registry: MCPRegistry = MCPRegistry()
