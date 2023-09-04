# PYTHON_ARGCOMPLETE_OK
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import logging
import argparse
import importlib
import pypdfium2 as pdfium  # yes this is legal in __main__
import pypdfium2.internal as pdfium_i
from pypdfium2.version import *

try:
    import argcomplete
except ImportError:
    argcomplete = None


SubCommands = {
    "arrange":        "rearrange/merge documents",
    "attachments":    "list/extract/edit embedded files",
    "extract-images": "extract images",
    "extract-text":   "extract text",
    "imgtopdf":       "convert images to PDF",
    "pageobjects":    "print info on page objects",
    "pdfinfo":        "print info on document and pages",
    "render":         "rasterize pages",
    "tile":           "tile pages (N-up)",
    "toc":            "print table of contents",
}

CmdToModule = {n: importlib.import_module(f"pypdfium2._cli.{n.replace('-', '_')}") for n in SubCommands}


def get_parser():
    
    main_parser = argparse.ArgumentParser(
        prog = "pypdfium2",
        description = "Command line interface to the pypdfium2 library (Python binding to PDFium)",
    )
    main_parser.add_argument(
        "--version", "-v",
        action = "version",
        version = f"pypdfium2 {V_PYPDFIUM2} (libpdfium {V_LIBPDFIUM}, origin: {V_BUILDNAME}, flags: {['V8', 'XFA'] if V_PDFIUM_IS_V8 else []})",
    )
    subparsers = main_parser.add_subparsers(dest="subcommand")
    
    for name, help in SubCommands.items():
        subparser = subparsers.add_parser(name, description=help, help=help)
        CmdToModule[name].attach(subparser)
    
    if argcomplete:
        argcomplete.autocomplete(main_parser)
    
    return main_parser


def setup_logging():
    
    pdfium_i.DEBUG_AUTOCLOSE.value = bool(int( os.environ.get("DEBUG_AUTOCLOSE", 0) ))
    
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
    
    CmdToModule[args.subcommand].main(args)


def cli_main():
    setup_logging()
    api_main()


if __name__ == "__main__":
    cli_main()
