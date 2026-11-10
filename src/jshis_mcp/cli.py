import asyncio
import json
import sys
from argparse import SUPPRESS, ArgumentParser
from collections.abc import Sequence

import httpx

from .client import (
    INTENSITY_PROBABILITIES,
    PROBABILITY_ATTRIBUTES,
    get_earthquake_hazard,
    get_hazard_intensity,
    get_surface_ground_amplification,
)


def run_cli(argv: Sequence[str]) -> None:
    parser = ArgumentParser(prog="jshis-mcp")
    commands = parser.add_subparsers(required=True)

    hazard = commands.add_parser(
        "get-earthquake-hazard",
        help="Get the J-SHIS hazard probability at a point.",
        argument_default=SUPPRESS,
    )
    hazard.add_argument("--minimum-jma-intensity", choices=PROBABILITY_ATTRIBUTES)
    hazard.set_defaults(handler=get_earthquake_hazard)

    intensity = commands.add_parser(
        "get-hazard-intensity",
        help="Get instrumental intensity at a specified exceedance probability.",
        argument_default=SUPPRESS,
    )
    intensity.add_argument("--period-years", type=int, choices=INTENSITY_PROBABILITIES)
    intensity.add_argument(
        "--exceedance-probability-percent",
        type=int,
        choices=sorted(value for values in INTENSITY_PROBABILITIES.values() for value in values),
    )
    intensity.set_defaults(handler=get_hazard_intensity)

    surface = commands.add_parser(
        "get-surface-ground-amplification",
        help="Get surface ground velocity amplification at a point.",
        argument_default=SUPPRESS,
    )
    surface.set_defaults(handler=get_surface_ground_amplification)

    for command in (hazard, intensity, surface):
        command.add_argument("--latitude", type=float, required=True)
        command.add_argument("--longitude", type=float, required=True)

    arguments = vars(parser.parse_args(argv))
    handler = arguments.pop("handler")
    try:
        result = asyncio.run(handler(**arguments))
        payload = result
    except (ValueError, OSError, httpx.HTTPError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
