from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from .client import get_area_geology, get_geology

READ_ONLY = ToolAnnotations(
    read_only_hint=True, idempotent_hint=True, destructive_hint=False, open_world_hint=True
)


def create_server() -> MCPServer:
    mcp = MCPServer("gsj-geology-mcp")
    mcp.tool(annotations=READ_ONLY)(get_geology)
    mcp.tool(annotations=READ_ONLY)(get_area_geology)
    return mcp
