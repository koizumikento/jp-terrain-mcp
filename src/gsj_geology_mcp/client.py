from decimal import Decimal
from typing import Annotated, Any

import httpx
from pydantic import Field, validate_call

SOURCE_URL = "https://gbank.gsj.jp/seamless/v2/api/1.3.1/"
API_URL = SOURCE_URL + "legend.json"
SOURCE = "AIST Geological Survey of Japan, Seamless Geological Map V2"
MAP_SCALE = "1:200000"
MAX_AREA_SPAN_DEGREES = Decimal("0.25")

Latitude = Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
Longitude = Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
Limit = Annotated[int, Field(ge=1, le=100)]
Offset = Annotated[int, Field(ge=0)]


async def _fetch_legend(parameter: str, value: str) -> Any:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(API_URL, params={parameter: value})
        response.raise_for_status()
    return response.json()


def _legend_fields(legend: dict[str, Any]) -> dict[str, str | None]:
    return {
        "symbol": legend["symbol"],
        "formation_age": legend.get("formationAge_ja"),
        "lithology": legend.get("lithology_ja"),
        "group": legend.get("group_ja"),
    }


@validate_call
async def get_geology(latitude: Latitude, longitude: Longitude) -> dict[str, str | float | None]:
    """Read the GSJ 1:200,000 geological map legend at a WGS84 point in Japan."""
    legend = await _fetch_legend("point", f"{latitude},{longitude}")
    if not isinstance(legend, dict) or not legend.get("symbol"):
        raise ValueError("The GSJ geological map has no legend at this point.")
    return {
        "latitude": latitude,
        "longitude": longitude,
        **_legend_fields(legend),
        "map_scale": MAP_SCALE,
        "source": SOURCE,
        "source_url": SOURCE_URL,
    }


@validate_call
async def get_area_geology(
    south: Latitude,
    west: Longitude,
    north: Latitude,
    east: Longitude,
    limit: Limit = 25,
    offset: Offset = 0,
) -> dict[str, Any]:
    """List geological map legends in a WGS84 box up to 0.25° tall and wide."""
    if south >= north or west >= east:
        raise ValueError("Provide south < north and west < east.")
    height = Decimal(str(north)) - Decimal(str(south))
    width = Decimal(str(east)) - Decimal(str(west))
    if max(height, width) > MAX_AREA_SPAN_DEGREES:
        raise ValueError("The area may span at most 0.25 degrees per side.")

    legends = await _fetch_legend("box", f"{south},{west},{north},{east}")
    if not isinstance(legends, list) or any(
        not isinstance(legend, dict)
        or not isinstance(legend.get("symbol"), str)
        or not legend["symbol"]
        for legend in legends
    ):
        raise ValueError("GSJ returned an invalid area legend response.")

    legends.sort(key=lambda legend: legend["symbol"])
    end = offset + limit
    return {
        "bounds": {"south": south, "west": west, "north": north, "east": east},
        "legends": [_legend_fields(legend) for legend in legends[offset:end]],
        "total": len(legends),
        "next_offset": end if end < len(legends) else None,
        "map_scale": MAP_SCALE,
        "source": SOURCE,
        "source_url": SOURCE_URL,
    }
