import httpx
import pytest
import respx
from pydantic import ValidationError

from gsi_elevation_mcp import ElevationPoint, get_elevation, get_elevations
from gsi_elevation_mcp.client import API_URL


@pytest.mark.asyncio
@respx.mock
async def test_elevation_and_unavailable_point() -> None:
    route = respx.get(API_URL).mock(
        side_effect=[
            httpx.Response(200, json={"elevation": 25.2, "hsrc": "5m（レーザ）"}),
            httpx.Response(200, json={"elevation": "-----", "hsrc": "-----"}),
        ]
    )
    result = await get_elevation(36.103543, 140.08531)
    assert result["elevation_m"] == 25.2
    assert result["measurement_source"] == "5m（レーザ）"
    assert route.calls[0].request.url.params["lon"] == "140.08531"
    assert (await get_elevation(0, 0))["elevation_m"] is None


@pytest.mark.asyncio
@respx.mock
async def test_compare_preserves_order_and_omits_unavailable_values_from_range() -> None:
    route = respx.get(API_URL).mock(
        side_effect=[
            httpx.Response(200, json={"elevation": 25.2, "hsrc": "5m（レーザ）"}),
            httpx.Response(200, json={"elevation": "-----", "hsrc": "-----"}),
            httpx.Response(200, json={"elevation": 15.1, "hsrc": "DEM10B"}),
        ]
    )
    points = [
        ElevationPoint(latitude=36.1, longitude=140.0),
        ElevationPoint(latitude=0, longitude=0),
        ElevationPoint(latitude=35.6, longitude=139.7),
    ]
    result = await get_elevations(points)
    assert isinstance(items := result["items"], list)
    assert [item["elevation_m"] for item in items] == [25.2, None, 15.1]
    assert result["elevation_range_m"] == 10.1
    assert [call.request.url.params["lon"] for call in route.calls] == ["140.0", "0.0", "139.7"]
    with pytest.raises(ValidationError):
        await get_elevations(points * 4)
    assert route.call_count == 3
