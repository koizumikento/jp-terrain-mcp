import asyncio
import json
import sys
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence

import httpx

from .client import get_elevation, get_elevations


def run_cli(argv: Sequence[str]) -> None:
    parser = ArgumentParser(prog="gsi-elevation-mcp")
    commands = parser.add_subparsers(required=True)

    command = commands.add_parser("get-elevation", argument_default=SUPPRESS)
    command.add_argument("--latitude", type=float, required=True)
    command.add_argument("--longitude", type=float, required=True)
    command.set_defaults(handler=get_elevation)

    command = commands.add_parser("get-elevations", argument_default=SUPPRESS)
    command.add_argument(
        "--point",
        dest="points",
        type=float,
        nargs=2,
        action="append",
        metavar=("LATITUDE", "LONGITUDE"),
        required=True,
    )
    command.set_defaults(handler=get_elevations)

    arguments = vars(parser.parse_args(argv))
    handler = arguments.pop("handler")
    if "points" in arguments:
        arguments["points"] = [
            {"latitude": latitude, "longitude": longitude}
            for latitude, longitude in arguments["points"]
        ]
    try:
        result = asyncio.run(handler(**arguments))
    except (ValueError, OSError, httpx.HTTPError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False) + "\n").encode("utf-8"))
