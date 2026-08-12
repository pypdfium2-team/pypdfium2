#! /usr/bin/env python3

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]/"setupsrc"))
from shared_base import install_dep_groups, _DEPGROUP_FALLBACK

parser = argparse.ArgumentParser()
parser.add_argument("groups", nargs="+")
parser.add_argument("-f", "--fallback", action="store_true", default=_DEPGROUP_FALLBACK)
args = parser.parse_args()

install_dep_groups(args.groups, need_fallback=args.fallback)
