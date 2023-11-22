#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import re
import sys
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
    search = run_cmd(["conda", "search", "pypdfium2_raw", "--override-channels", "-c", "pypdfium2-team"], cwd=None, capture=True)
    print(search, file=sys.stderr)
    
    search = [(int(v), int(b.split("_")[1])) for (v, b) in [re.split(r"\s+", l)[1:3] for l in reversed(search.split("\n")[2:])]]
    print(search, file=sys.stderr)
    
    # determine build number
    # TODO `search` is ordered descendingly, so we could break the iteration when we find a match. though for a new version, we have to traverse the full list anyway...
    build = max([b for v, b in search if v == args.pdfium_ver], default=None)
    build = 0 if build is None else build+1
    print(build, file=sys.stderr)
    
    # store build number in a file for use in a subsequent craft_packages call
    CondaRaw_BuildNumF.write_text(str(build))


if __name__ == "__main__":
    main()
