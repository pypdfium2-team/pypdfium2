# PYTHON_ARGCOMPLETE_OK
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import logging
import argparse
from pypdfium2.version import (
    V_PYPDFIUM2,
    V_LIBPDFIUM,
    IS_SOURCEBUILD,
)
from pypdfium2._cli import (
    render,
    toc,
    merge,
    tile,
    extract_text,
    find_pageobjects,
    jpegtopdf,
)

try:
    import argcomplete
except ImportError:
    argcomplete = None


Subcommands = {
    "render": render,
    "toc": toc,
    "merge": merge,
    "tile": tile,
    "extract-text": extract_text,
    "find-pageobjects": find_pageobjects,
    "jpegtopdf": jpegtopdf,
}


def parse_args(argv=sys.argv[1:]):
    
    parser = argparse.ArgumentParser(
        prog = "pypdfium2",
        description = "Command line interface to the pypdfium2 Python library",
    )
    parser.add_argument(
        "--version", "-v",
        action = "version",
        version = "pypdfium2 %s (libpdfium %s, %s)" % (
            V_PYPDFIUM2, V_LIBPDFIUM,
            "source build" if IS_SOURCEBUILD else "official build",
        ),
    )
    
    subparsers = parser.add_subparsers(dest="subcommand")
    for cmd in Subcommands.values():
        cmd.attach_parser(subparsers)
    
    if argcomplete is not None:
        argcomplete.autocomplete(parser)
    
    return parser.parse_args(argv)


def main():
    
    lib_logger = logging.getLogger("pypdfium2")
    lib_logger.addHandler(logging.StreamHandler())
    
    args = parse_args()
    if not args.subcommand:
        print("One of the following subcommands must be given: %s" % [sc for sc in Subcommands.keys()])
        return
    
    Subcommands[args.subcommand].main(args)
