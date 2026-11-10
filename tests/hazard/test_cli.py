import json
from unittest.mock import AsyncMock

import pytest

from jshis_mcp import cli


def test_cli_uses_public_function(
    monkeypatch: pytest.MonkeyPatch, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    payload = {"name": "日本語"}
    handler = AsyncMock(return_value=payload)
    monkeypatch.setattr(cli, "get_earthquake_hazard", handler)
    args = ["get-earthquake-hazard", "--latitude", "35.6812", "--longitude", "139.7671"]
    cli.run_cli(args)
    handler.assert_awaited_once_with(**{"latitude": 35.6812, "longitude": 139.7671})
    assert json.loads(capsysbinary.readouterr().out) == payload


def test_cli_passes_period_and_probability(
    monkeypatch: pytest.MonkeyPatch, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    handler = AsyncMock(return_value={"instrumental_intensity": 5.25})
    monkeypatch.setattr(cli, "get_hazard_intensity", handler)
    cli.run_cli(
        [
            "get-hazard-intensity",
            "--latitude",
            "35.6812",
            "--longitude",
            "139.7671",
            "--period-years",
            "50",
            "--exceedance-probability-percent",
            "5",
        ]
    )
    handler.assert_awaited_once_with(
        latitude=35.6812, longitude=139.7671, period_years=50, exceedance_probability_percent=5
    )
    assert json.loads(capsysbinary.readouterr().out) == {"instrumental_intensity": 5.25}
