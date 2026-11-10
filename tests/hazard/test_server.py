import json
import sys

import httpx
import pytest
import respx
from mcp import Client, StdioServerParameters
from mcp.types import TextContent

from jshis_mcp import create_server, get_earthquake_hazard, get_hazard_intensity
from jshis_mcp.client import API_URL, SURFACE_API_URL

# Mock responses use invented values. The mesh code is a placeholder.
SYNTHETIC_MESH_CODE = "0000000000"


@pytest.mark.asyncio
async def test_stdio_tools() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "jshis_mcp"])
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.list_tools()
    assert {tool.name for tool in result.tools} == {
        "get_earthquake_hazard",
        "get_hazard_intensity",
        "get_surface_ground_amplification",
    }
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in result.tools)


@pytest.mark.asyncio
@respx.mock
async def test_model_probability_and_coordinates() -> None:
    route = respx.get(
        API_URL, params={"position": "139.75,35.5", "epsg": 4326, "attr": "T30_I55_PS"}
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "Success",
                "metaData": {"version": "Y2024", "case": "AVR", "eqcode": "TTL_MTTL"},
                "features": [
                    {"properties": {"meshcode": SYNTHETIC_MESH_CODE, "T30_I55_PS": "0.375"}}
                ],
            },
        )
    )
    async with Client(create_server()) as client:
        result = await client.call_tool(
            "get_earthquake_hazard", {"latitude": 35.5, "longitude": 139.75}
        )
        invalid = await client.call_tool(
            "get_earthquake_hazard", {"latitude": 140, "longitude": 35}
        )
    assert route.call_count == 1
    assert not result.is_error
    assert isinstance(result.content[0], TextContent)
    payload = json.loads(result.content[0].text)
    assert payload["probability_percent"] == 37.5
    assert payload["model_version"] == "Y2024"
    assert invalid.is_error


@pytest.mark.asyncio
@respx.mock
async def test_threshold_probability_and_period_intensity_use_distinct_attributes() -> None:
    for attribute, value in (("T30_I45_PS", "0.7125"), ("T50_P05_SI", "5.25")):
        respx.get(
            API_URL, params={"position": "139.75,35.5", "epsg": 4326, "attr": attribute}
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": "Success",
                    "metaData": {"version": "Y2024", "case": "AVR", "eqcode": "TTL_MTTL"},
                    "features": [
                        {"properties": {"meshcode": SYNTHETIC_MESH_CODE, attribute: value}}
                    ],
                },
            )
        )
    hazard = await get_earthquake_hazard(35.5, 139.75, minimum_jma_intensity="5-lower")
    assert hazard["probability_percent"] == pytest.approx(71.25)
    assert hazard["period_years"] == 30
    intensity = await get_hazard_intensity(35.5, 139.75, period_years=50)
    assert intensity["instrumental_intensity"] == 5.25
    assert intensity["exceedance_probability_percent"] == 5
    with pytest.raises(ValueError, match="supports 3%, 6% for 30 years"):
        await get_hazard_intensity(35.5, 139.75, 30, 5)
    assert respx.calls.call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_surface_ground_amplification_uses_surface_model() -> None:
    route = respx.get(SURFACE_API_URL, params={"position": "139.75,35.5", "epsg": 4326})
    route.mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "Success",
                "metaData": {"version": "V4"},
                "features": [
                    {
                        "properties": {
                            "meshcode": SYNTHETIC_MESH_CODE,
                            "ARV": "1.5",
                            "AVS": "250.5",
                            "JCODE": "00",
                            "JNAME": "架空の地形区分",
                        }
                    }
                ],
            },
        )
    )
    async with Client(create_server()) as client:
        result = await client.call_tool(
            "get_surface_ground_amplification", {"latitude": 35.5, "longitude": 139.75}
        )
    assert route.call_count == 1
    assert not result.is_error
    assert isinstance(result.content[0], TextContent)
    payload = json.loads(result.content[0].text)
    assert payload["mesh_code"] == SYNTHETIC_MESH_CODE
    assert payload["velocity_amplification_factor"] == 1.5
    assert payload["average_s_wave_velocity_m_per_s"] == 250.5
    assert payload["geomorphology_code"] == "00"
    assert payload["geomorphology_name"] == "架空の地形区分"
    assert payload["model_version"] == "V4"
