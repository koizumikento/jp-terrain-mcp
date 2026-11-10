from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from .client import get_earthquake_hazard, get_hazard_intensity, get_surface_ground_amplification

READ_ONLY = ToolAnnotations(
    read_only_hint=True, idempotent_hint=True, destructive_hint=False, open_world_hint=True
)


def create_server() -> MCPServer:
    mcp = MCPServer("jshis-mcp")
    mcp.tool(annotations=READ_ONLY)(get_earthquake_hazard)
    mcp.tool(annotations=READ_ONLY)(get_hazard_intensity)
    mcp.tool(annotations=READ_ONLY)(get_surface_ground_amplification)
    return mcp
