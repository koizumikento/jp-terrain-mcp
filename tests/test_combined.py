import subprocess
import sys

import pytest
from mcp import Client, StdioServerParameters

from gsi_elevation_mcp import cli as elevation_cli
from gsi_elevation_mcp.server import create_server as elevation_server
from gsj_geology_mcp import cli as geology_cli
from gsj_geology_mcp.server import create_server as geology_server
from jp_terrain_mcp import create_server
from jp_terrain_mcp.cli import run_cli
from jshis_mcp import cli as hazard_cli
from jshis_mcp.server import create_server as hazard_server


@pytest.mark.asyncio
async def test_combined_tools_preserve_source_schemas() -> None:
    expected = []
    for factory in (
        elevation_server,
        geology_server,
        hazard_server,
    ):
        expected.extend(await factory().list_tools())
    actual = await create_server().list_tools()
    assert len(actual) == 7
    assert len({tool.name for tool in actual}) == len(actual)
    assert {tool.name: tool.model_dump(exclude_none=True) for tool in actual} == {
        tool.name: tool.model_dump(exclude_none=True) for tool in expected
    }


@pytest.mark.asyncio
async def test_combined_stdio_lists_all_tools() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "jp_terrain_mcp"])
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.list_tools()
    assert len(result.tools) == 7
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in result.tools)


@pytest.mark.parametrize(
    "group, module",
    [("elevation", elevation_cli), ("geology", geology_cli), ("hazard", hazard_cli)],
)
def test_cli_dispatches_without_changing_arguments(monkeypatch, group, module) -> None:
    calls = []
    monkeypatch.setattr(module, "run_cli", lambda args: calls.append(list(args)))
    from jp_terrain_mcp import cli

    monkeypatch.setattr(cli, group.replace("-", "_") + "_cli", module.run_cli)
    run_cli([group, "query", "--limit", "2"])
    assert calls == [["query", "--limit", "2"]]


def test_command_help() -> None:
    for group in ["elevation", "geology", "hazard"]:
        result = subprocess.run(
            [sys.executable, "-m", "jp_terrain_mcp", group, "--help"],
            capture_output=True,
            check=True,
        )
        assert b"usage:" in result.stdout
