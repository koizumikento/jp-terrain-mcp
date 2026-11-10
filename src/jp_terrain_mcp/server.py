from mcp.server import MCPServer

from gsi_elevation_mcp import server as elevation_server
from gsj_geology_mcp import server as geology_server
from jshis_mcp import server as hazard_server


def create_server() -> MCPServer:
    mcp = MCPServer("jp-terrain-mcp")
    mcp.tool(annotations=elevation_server.READ_ONLY)(
        elevation_server._tool_errors(elevation_server.get_elevation)
    )
    mcp.tool(annotations=elevation_server.READ_ONLY)(
        elevation_server._tool_errors(elevation_server.get_elevations)
    )
    mcp.tool(annotations=geology_server.READ_ONLY)(geology_server.get_geology)
    mcp.tool(annotations=geology_server.READ_ONLY)(geology_server.get_area_geology)
    mcp.tool(annotations=hazard_server.READ_ONLY)(hazard_server.get_earthquake_hazard)
    mcp.tool(annotations=hazard_server.READ_ONLY)(hazard_server.get_hazard_intensity)
    mcp.tool(annotations=hazard_server.READ_ONLY)(hazard_server.get_surface_ground_amplification)
    return mcp
