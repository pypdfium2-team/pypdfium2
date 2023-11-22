#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import json
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))
from pypdfium2_setup.packaging_base import *


def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdfium-ver", type=int, default=None)
    args = parser.parse_args()
    if not args.pdfium_ver or args.pdfium_ver == "latest":
        args.pdfium_ver = PdfiumVer.get_latest()
    else:
        args.pdfium_ver = int(args.pdfium_ver)
    
    # parse existing releases to automatically handle arbitrary version builds
    search = run_cmd(["conda", "search", "--json", "pypdfium2_raw", "--override-channels", "-c", "pypdfium2-team"], cwd=None, capture=True)
    search = reversed(json.loads(search)["pypdfium2_raw"])
    
    # determine build number
    # TODO `search` seems to be ordered by date, so we could probably break the iteration when we find a matching version. though for a new version, we have to traverse the full list anyway...
    build = max([d["build_number"] for d in search if int(d["version"]) == args.pdfium_ver], default=None)
    build = 0 if build is None else build+1
    print(build, file=sys.stderr)
    
    # store build number in a file for use in a subsequent craft_packages call
    CondaRaw_BuildNumF.write_text(str(build))


if __name__ == "__main__":
    main()
