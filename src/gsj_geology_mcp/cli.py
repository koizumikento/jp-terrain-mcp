import asyncio
import json
import sys
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence

import httpx

from .client import get_area_geology, get_geology


def run_cli(argv: Sequence[str]) -> None:
    parser = ArgumentParser(prog="gsj-geology-mcp")
    commands = parser.add_subparsers(required=True)

    command = commands.add_parser(
        "get-geology", help="Get the geological map legend at a point.", argument_default=SUPPRESS
    )
    command.add_argument("--latitude", type=float, required=True)
    command.add_argument("--longitude", type=float, required=True)
    command.set_defaults(handler=get_geology)

    area = commands.add_parser(
        "get-area-geology",
        help="List geological map legends within a bounding box.",
        argument_default=SUPPRESS,
    )
    for side in ("south", "west", "north", "east"):
        area.add_argument(f"--{side}", type=float, required=True)
    area.add_argument("--limit", type=int)
    area.add_argument("--offset", type=int)
    area.set_defaults(handler=get_area_geology)

    arguments = vars(parser.parse_args(argv))
    handler = arguments.pop("handler")
    try:
        result = asyncio.run(handler(**arguments))
        payload = result
    except (ValueError, OSError, httpx.HTTPError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
