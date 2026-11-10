import json
import sys

import httpx
import pytest
import respx
from mcp import Client, StdioServerParameters
from mcp.types import TextContent

from gsj_geology_mcp import create_server, get_area_geology
from gsj_geology_mcp.client import API_URL


@pytest.mark.asyncio
async def test_stdio_tools() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "gsj_geology_mcp"])
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.list_tools()
    assert {tool.name for tool in result.tools} == {"get_geology", "get_area_geology"}
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in result.tools)


@pytest.mark.asyncio
@respx.mock
async def test_legend_and_coordinate_order() -> None:
    route = respx.get(API_URL, params={"point": "39.5,141.25"}).mock(
        return_value=httpx.Response(
            200, json={"symbol": "unit", "formationAge_ja": "age", "lithology_ja": "rock"}
        )
    )
    async with Client(create_server()) as client:
        result = await client.call_tool("get_geology", {"latitude": 39.5, "longitude": 141.25})
    assert route.called
    assert not result.is_error
    assert isinstance(result.content[0], TextContent)
    payload = json.loads(result.content[0].text)
    assert payload["lithology"] == "rock"
    assert payload["formation_age"] == "age"
    assert payload["map_scale"] == "1:200000"


@pytest.mark.asyncio
@respx.mock
async def test_area_coordinate_order_sorted_page_and_limits() -> None:
    route = respx.get(API_URL, params={"box": "39.69,141.13,39.71,141.16"}).mock(
        return_value=httpx.Response(
            200,
            json=[
                {"symbol": "Z", "lithology_ja": "堆積岩"},
                {"symbol": "A", "formationAge_ja": "第四紀"},
                {"symbol": "H"},
            ],
        )
    )
    bounds = {"south": 39.69, "west": 141.13, "north": 39.71, "east": 141.16}
    async with Client(create_server()) as client:
        result = await client.call_tool("get_area_geology", {**bounds, "limit": 1, "offset": 1})
    assert not result.is_error
    assert isinstance(result.content[0], TextContent)
    payload = json.loads(result.content[0].text)
    assert payload["bounds"] == bounds
    assert [legend["symbol"] for legend in payload["legends"]] == ["H"]
    assert payload["next_offset"] == 2
    assert payload["total"] == 3
    assert payload["map_scale"] == "1:200000"
    with pytest.raises(ValueError, match="at most 0.25 degrees"):
        await get_area_geology(39.69, 141.13, 40.0, 141.16)
    with pytest.raises(ValueError, match="south < north and west < east"):
        await get_area_geology(39.71, 141.13, 39.69, 141.16)
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_area_empty_coverage_at_maximum_span() -> None:
    respx.get(API_URL, params={"box": "0.0,141.13,0.25,141.38"}).mock(
        return_value=httpx.Response(200, json=[])
    )
    payload = await get_area_geology(0.0, 141.13, 0.25, 141.38)
    assert payload["legends"] == []
    assert payload["next_offset"] is None
    assert payload["total"] == 0
