# PYTHON_ARGCOMPLETE_OK
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import argparse
from pypdfium2._version import (
    V_PYPDFIUM2,
    V_LIBPDFIUM,
)
from pypdfium2._cli import (
    render,
    toc,
    merge,
    tile,
)

try:
    import argcomplete
except ImportError:
    have_argcomplete = False
else:
    have_argcomplete = True


Subcommands = dict(
    render = render,
    toc = toc,
    merge = merge,
    tile = tile,
)


def parse_args(argv=sys.argv[1:]):
    
    parser = argparse.ArgumentParser(
        prog = "pypdfium2",
        description = "Command line interface to the pypdfium2 Python library",
    )
    parser.add_argument(
        "--version", "-v",
        action = "version",
        version = "pypdfium2 %s (libpdfium %s)" % (V_PYPDFIUM2, V_LIBPDFIUM),
    )
    
    subparsers = parser.add_subparsers(dest="subcommand")
    for cmd in Subcommands.values():
        cmd.attach_parser(subparsers)
    
    if have_argcomplete:
        argcomplete.autocomplete(parser)
    
    return parser.parse_args(argv)


def main():
    args = parse_args()
    if not args.subcommand:
        print("One of the following subcommands must be given: %s" % [sc for sc in Subcommands.keys()])
        return
    Subcommands[args.subcommand].main(args)
