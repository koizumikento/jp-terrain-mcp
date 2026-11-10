import sys

import pytest
from mcp import Client, StdioServerParameters

from gsi_elevation_mcp import create_server


@pytest.mark.asyncio
async def test_stdio_tool_contract() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "gsi_elevation_mcp"])
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.list_tools()
    assert {tool.name for tool in result.tools} == {"get_elevation", "get_elevations"}
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in result.tools)
    assert len(await create_server().list_tools()) == 2
