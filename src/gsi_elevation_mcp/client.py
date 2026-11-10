import math
from typing import Annotated

import httpx
from pydantic import BaseModel, ConfigDict, Field, validate_call

SOURCE_URL = "https://maps.gsi.go.jp/development/elevation_s.html"
API_URL = "https://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php"

Latitude = Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
Longitude = Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
Elevation = dict[str, str | float | None]


class ElevationPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: Latitude
    longitude: Longitude


async def _read_elevation(
    client: httpx.AsyncClient, latitude: float, longitude: float
) -> Elevation:
    response = await client.get(
        API_URL, params={"lat": latitude, "lon": longitude, "outtype": "JSON"}
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or not {"elevation", "hsrc"} <= payload.keys():
        raise ValueError("GSI returned an unexpected elevation response.")
    elevation = payload["elevation"]
    source = payload["hsrc"]
    if elevation == source == "-----":
        elevation = source = None
    elif (
        type(elevation) not in (int, float)
        or not math.isfinite(elevation)
        or not isinstance(source, str)
        or source == "-----"
    ):
        raise ValueError("GSI returned an invalid elevation or measurement source.")
    return {
        "latitude": latitude,
        "longitude": longitude,
        "elevation_m": elevation,
        "measurement_source": source,
        "source_url": SOURCE_URL,
    }


@validate_call
async def get_elevation(latitude: Latitude, longitude: Longitude) -> Elevation:
    """Read the GSI elevation in metres and its measurement source at a WGS84 point."""
    async with httpx.AsyncClient(timeout=15) as client:
        return await _read_elevation(client, latitude, longitude)


@validate_call
async def get_elevations(
    points: Annotated[list[ElevationPoint], Field(min_length=1, max_length=10)],
) -> dict[str, list[Elevation] | float | None]:
    """Compare GSI elevations for 1 to 10 supplied WGS84 points in input order."""
    async with httpx.AsyncClient(timeout=15) as client:
        items = [await _read_elevation(client, point.latitude, point.longitude) for point in points]
    elevations = [value for item in items if isinstance(value := item["elevation_m"], (int, float))]
    return {
        "items": items,
        "elevation_range_m": round(max(elevations) - min(elevations), 1)
        if len(elevations) >= 2
        else None,
    }
