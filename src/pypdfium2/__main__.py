# PYTHON_ARGCOMPLETE_OK
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import argparse
import importlib
from pypdfium2.version import *
from pypdfium2._cli._parsers import setup_logging

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
        version = f"pypdfium2 {V_PYPDFIUM2} (libpdfium {V_LIBPDFIUM}, {V_BUILDNAME} {'V8' if V_PDFIUM_IS_V8 else 'default'} build)",
    )
    subparsers = main_parser.add_subparsers(dest="subcommand")
    
    for name, help in SubCommands.items():
        subparser = subparsers.add_parser(name, description=help, help=help)
        CmdToModule[name].attach(subparser)
    
    if argcomplete:
        argcomplete.autocomplete(main_parser)
    
    return main_parser


def main(argv):
    """
    API entrypoint to pypdfium2's command-line interface.
    See :doc:`./shell_api` or ``pypdfium2 --help``.
    
    Parameters:
        argv (list[str]):
            The command-line arguments.
    
    Example:
        
        .. code-block:: python
            
            # rendering
            main(["render", "my_file.pdf", "-o=out/", "--prefix=result_", "--scale=4", "--rev-byteorder", "--prefer-bgrx"])
    """
    
    parser = get_parser()
    args = parser.parse_args(argv)
    
    if not args.subcommand:
        parser.print_help()
        return
    
    CmdToModule[args.subcommand].main(args)


def cli_main():
    setup_logging()
    main(sys.argv[1:])


if __name__ == "__main__":
    cli_main()
