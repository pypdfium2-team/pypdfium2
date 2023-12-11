# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import argparse
import importlib
from pypdfium2.version import PYPDFIUM_INFO, PDFIUM_INFO
from pypdfium2._cli._parsers import setup_logging

try:
    from pypdfium2_raw.bindings import _libs_info
    pdfium_path = _libs_info["pdfium"]["path"]
except ImportError:
    # retained for downward compatibility with conda pypdfium2_raw <= 6164 by date of initial build
    # actually it's the ctypesgen version that matters, but we don't have info about that
    from pypdfium2_raw.bindings import _loader_info
    pdfium_path = _loader_info["libpath"]

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
        formatter_class = argparse.RawTextHelpFormatter,
        description = "Command line interface to the pypdfium2 library (Python binding to PDFium)",
    )
    main_parser.add_argument(
        "--version", "-v",
        action = "version",
        version = f"pypdfium2 {PYPDFIUM_INFO}\n" f"pdfium {PDFIUM_INFO} at {pdfium_path}"
    )
    subparsers = main_parser.add_subparsers(dest="subcommand")
    
    for name, help in SubCommands.items():
        subparser = subparsers.add_parser(name, description=help, help=help)
        CmdToModule[name].attach(subparser)
    
    return main_parser


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
