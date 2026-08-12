#! /usr/bin/env python3

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]/"setupsrc"))
from shared_base import install_dep_groups, _DEPGROUP_FALLBACK
from stl import BooleanOptionalAction  # shared

parser = argparse.ArgumentParser(
    description="Install a pyproject.toml dependency group (PEP 735) in a backward compatibility agnostic way.",
)
parser.add_argument("groups", nargs="+")
parser.add_argument(
    "--fallback",
    action=BooleanOptionalAction,
    default=_DEPGROUP_FALLBACK,
)
args = parser.parse_args()

install_dep_groups(args.groups, use_fallback=args.fallback)
