from argparse import ArgumentParser
from collections.abc import Sequence

from gsi_elevation_mcp.cli import run_cli as elevation_cli
from gsj_geology_mcp.cli import run_cli as geology_cli
from jshis_mcp.cli import run_cli as hazard_cli


def run_cli(argv: Sequence[str]) -> None:
    parser = ArgumentParser(prog="jp-terrain-mcp")
    commands = parser.add_subparsers(required=True)
    commands.add_parser("elevation", help="国土地理院の標高", add_help=False).set_defaults(
        handler=elevation_cli
    )
    commands.add_parser("geology", help="産総研の地質図", add_help=False).set_defaults(
        handler=geology_cli
    )
    commands.add_parser("hazard", help="J-SHISの地震ハザード", add_help=False).set_defaults(
        handler=hazard_cli
    )
    arguments, remaining = parser.parse_known_args(argv)
    arguments.handler(remaining)
