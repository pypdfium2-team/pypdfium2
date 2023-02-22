# PYTHON_ARGCOMPLETE_OK
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import logging
import argparse
import importlib
import pypdfium2._helpers as pdfium
from pypdfium2._helpers._internal import bases
from pypdfium2.version import *

try:
    import argcomplete
except ImportError:
    argcomplete = None


SubCommands = {
    "render":         "rasterize pages",
    "toc":            "print table of contents",
    "arrange":        "rearrange/merge documents",
    "tile":           "tile pages (N-up)",
    "pdfinfo":        "print info on document and pages",
    "pageobjects":    "print info on page objects",
    "extract-text":   "extract text",
    "extract-images": "extract images",
    "imgtopdf":       "convert images to PDF",
    "attachments":    "list/extract/edit embedded files",
}

CmdToModule = {n: importlib.import_module("pypdfium2._cli.%s" % n.replace("-", "_")) for n in SubCommands}


def get_parser():
    
    main_parser = argparse.ArgumentParser(
        prog = "pypdfium2",
        description = "Command line interface to the pypdfium2 library (Python binding to PDFium)",
    )
    main_parser.add_argument(
        "--version", "-v",
        action = "version",
        version = "pypdfium2 %s (libpdfium %s, %s build)" % (V_PYPDFIUM2, V_LIBPDFIUM, V_BUILDNAME),
    )
    subparsers = main_parser.add_subparsers(dest="subcommand")
    
    for name, help in SubCommands.items():
        subparser = subparsers.add_parser(name, description=help, help=help)
        module = CmdToModule[name]
        module.attach(subparser)
    
    if argcomplete is not None:
        argcomplete.autocomplete(main_parser)
    
    return main_parser


def setup_logging():
    
    # FIXME can we make some sort of public API to set this without a strange import?
    bases.DEBUG_AUTOCLOSE = bool(int( os.environ.get("DEBUG_AUTOCLOSE", "0") ))
    
    lib_logger = logging.getLogger("pypdfium2")
    lib_logger.addHandler(logging.StreamHandler())
    lib_logger.setLevel(logging.DEBUG)
    
    pdfium.PdfUnspHandler().setup()


def api_main(raw_args=sys.argv[1:]):
    
    parser = get_parser()
    args = parser.parse_args(raw_args)
    if not args.subcommand:
        parser.print_help()
        return
    
    module = CmdToModule[args.subcommand]
    module.main(args)


def cli_main():
    setup_logging()
    api_main()


if __name__ == "__main__":
    cli_main()
