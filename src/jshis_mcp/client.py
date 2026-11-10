from math import isfinite
from typing import Annotated, Any, Literal

import httpx
from pydantic import Field, validate_call

SOURCE_URL = "https://www.j-shis.bosai.go.jp/api-pshm-meshinfo"
MODEL_VERSION = "Y2024"
ATTRIBUTE = "T30_I55_PS"
SURFACE_SOURCE_URL = "https://www.j-shis.bosai.go.jp/api-sstruct-meshinfo"
SURFACE_API_URL = "https://www.j-shis.bosai.go.jp/map/api/sstrct/V4/meshinfo.geojson"
API_URL = (
    f"https://www.j-shis.bosai.go.jp/map/api/pshm/{MODEL_VERSION}/AVR/TTL_MTTL/meshinfo.geojson"
)

Latitude = Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
Longitude = Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
MinimumJmaIntensity = Literal["5-lower", "5-upper", "6-lower", "6-upper"]
HazardPeriod = Literal[30, 50]
ExceedanceProbability = Literal[2, 3, 5, 6, 10, 39]
PROBABILITY_ATTRIBUTES = {
    "5-lower": "T30_I45_PS",
    "5-upper": "T30_I50_PS",
    "6-lower": ATTRIBUTE,
    "6-upper": "T30_I60_PS",
}
INTENSITY_PROBABILITIES = {30: (3, 6), 50: (5, 2, 10, 39)}


async def _mesh_properties(
    api_url: str, latitude: float, longitude: float, attribute: str | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    params: dict[str, str | int] = {"position": f"{longitude},{latitude}", "epsg": 4326}
    if attribute is not None:
        params["attr"] = attribute
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(api_url, params=params)
        response.raise_for_status()

    data = response.json()
    if data.get("status") != "Success":
        code = (data.get("error") or {}).get("code", "UNKNOWN")
        raise ValueError(f"J-SHIS returned {code} for the requested location.")
    features = data.get("features") or []
    if len(features) != 1 or not features[0].get("properties"):
        raise ValueError("J-SHIS has no mesh data for this location.")
    return features[0]["properties"], data["metaData"]


def _read_number(properties: dict[str, Any], attribute: str) -> float:
    value = properties.get(attribute)
    if value is None:
        raise ValueError(f"J-SHIS has no {attribute} value for this location.")
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"J-SHIS returned an invalid {attribute} value.")
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"J-SHIS returned an invalid {attribute} value.")
    return number


@validate_call
async def get_earthquake_hazard(
    latitude: Latitude, longitude: Longitude, minimum_jma_intensity: MinimumJmaIntensity = "6-lower"
) -> dict[str, str | float | int]:
    """Read the 30-year probability of meeting or exceeding a JMA intensity at a WGS84 point."""
    attribute = PROBABILITY_ATTRIBUTES[minimum_jma_intensity]
    properties, metadata = await _mesh_properties(API_URL, latitude, longitude, attribute)
    probability = _read_number(properties, attribute)
    if not 0 <= probability <= 1:
        raise ValueError("J-SHIS returned an invalid hazard probability.")
    return {
        "latitude": latitude,
        "longitude": longitude,
        "mesh_code": properties["meshcode"],
        "model_version": metadata["version"],
        "probability_case": metadata["case"],
        "earthquake_category": metadata["eqcode"],
        "period_years": 30,
        "minimum_jma_intensity": minimum_jma_intensity,
        "probability_percent": probability * 100,
        "source": "NIED J-SHIS",
        "source_url": SOURCE_URL,
        "source_attribute": attribute,
    }


@validate_call
async def get_hazard_intensity(
    latitude: Latitude,
    longitude: Longitude,
    period_years: HazardPeriod = 30,
    exceedance_probability_percent: ExceedanceProbability | None = None,
) -> dict[str, str | float | int]:
    """Read instrumental intensity at a specified exceedance probability at a WGS84 point.

    Choose 3% or 6% for 30 years (default 3%), or 2%, 5%, 10% or 39% for 50 years (default 5%).
    """
    allowed = INTENSITY_PROBABILITIES[period_years]
    probability = (
        allowed[0] if exceedance_probability_percent is None else exceedance_probability_percent
    )
    if probability not in allowed:
        choices = ", ".join(f"{value}%" for value in sorted(allowed))
        raise ValueError(f"J-SHIS supports {choices} for {period_years} years.")
    attribute = f"T{period_years}_P{probability:02d}_SI"
    properties, metadata = await _mesh_properties(API_URL, latitude, longitude, attribute)
    return {
        "latitude": latitude,
        "longitude": longitude,
        "mesh_code": properties["meshcode"],
        "model_version": metadata["version"],
        "probability_case": metadata["case"],
        "earthquake_category": metadata["eqcode"],
        "period_years": period_years,
        "exceedance_probability_percent": probability,
        "instrumental_intensity": _read_number(properties, attribute),
        "source": "NIED J-SHIS",
        "source_url": SOURCE_URL,
        "source_attribute": attribute,
    }


@validate_call
async def get_surface_ground_amplification(
    latitude: Latitude, longitude: Longitude
) -> dict[str, str | float | int | None]:
    """Read surface ground velocity amplification and geomorphology at a WGS84 point."""
    properties, metadata = await _mesh_properties(SURFACE_API_URL, latitude, longitude)
    amplification = _read_number(properties, "ARV")
    if amplification <= 0:
        raise ValueError("J-SHIS returned an invalid surface ground amplification factor.")
    return {
        "latitude": latitude,
        "longitude": longitude,
        "mesh_code": properties["meshcode"],
        "model_version": metadata["version"],
        "velocity_amplification_factor": amplification,
        "average_s_wave_velocity_m_per_s": (
            _read_number(properties, "AVS") if properties.get("AVS") is not None else None
        ),
        "geomorphology_code": properties.get("JCODE"),
        "geomorphology_name": properties.get("JNAME"),
        "source": "NIED J-SHIS",
        "source_url": SURFACE_SOURCE_URL,
        "source_attribute": "ARV",
    }
