import json
from unittest.mock import AsyncMock

import pytest

from gsj_geology_mcp import cli


def test_cli_uses_public_function(
    monkeypatch: pytest.MonkeyPatch, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    payload = {"name": "日本語"}
    handler = AsyncMock(return_value=payload)
    monkeypatch.setattr(cli, "get_geology", handler)
    args = ["get-geology", "--latitude", "39.700038", "--longitude", "141.149898"]
    cli.run_cli(args)
    handler.assert_awaited_once_with(**{"latitude": 39.700038, "longitude": 141.149898})
    assert json.loads(capsysbinary.readouterr().out) == payload


def test_cli_uses_area_function(
    monkeypatch: pytest.MonkeyPatch, capsysbinary: pytest.CaptureFixture[bytes]
) -> None:
    handler = AsyncMock(return_value={"legends": []})
    monkeypatch.setattr(cli, "get_area_geology", handler)
    cli.run_cli(
        [
            "get-area-geology",
            "--south",
            "39.69",
            "--west",
            "141.13",
            "--north",
            "39.71",
            "--east",
            "141.16",
            "--limit",
            "3",
        ]
    )
    handler.assert_awaited_once_with(south=39.69, west=141.13, north=39.71, east=141.16, limit=3)
    assert json.loads(capsysbinary.readouterr().out) == {"legends": []}
