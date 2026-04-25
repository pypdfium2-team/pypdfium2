# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import argparse
import importlib
from os.path import basename
# Important: Do not import from the core `pypdfium2` module here, because it initializes the library, which must be deferred until after setup_logging(). Importing from the other modules (e.g. pypdfium2_cli itself) is fine.
from pypdfium2_cli._setup import setup_logging

SubCommands = {
    "arrange":        "Rearrange/merge documents",
    "attachments":    "List/extract/edit embedded files",
    "extract-images": "Extract images",
    "extract-text":   "Extract text",
    "imgtopdf":       "Convert images to PDF",
    "pageobjects":    "Print info on pageobjects",
    "pdfinfo":        "Print info on document and pages",
    "fonts":          "List a document's fonts",
    "render":         "Rasterize pages",
    "tile":           "Tile pages (N-up)",
    "toc":            "Print table of contents",
}

def get_version():
    from pypdfium2.version import PYPDFIUM_INFO, PDFIUM_INFO
    from pypdfium2_raw.bindings import _libs
    return f"pypdfium2 {PYPDFIUM_INFO}\npdfium {PDFIUM_INFO} at {_libs['pdfium']._name}"


def get_parser(argv):
    
    main_parser = argparse.ArgumentParser(
        prog = "pypdfium2",
        formatter_class = argparse.RawTextHelpFormatter,
        description = """\
pypdfium2 is a Python binding to PDFium, a PDF processing library.
This is the command-line interface. Invoke as `pypdfium2` or `%(py_exe)s -m pypdfium2_cli`.

pypdfium2's CLI mainly serves testing purposes, similar to pdfium_test upstream.
No API stability promises are being made.

Environment variables:
- PYPDFIUM_LOGLEVEL {debug,info,warning,error,critical} = debug
  Controls the logging level.
- DEBUG_AUTOCLOSE {0,1} = 0
  Print debug info when PDFium objects are (auto-)closed.
- DEBUG_UNSUPPORTED {0,1} = 1
  Whether to enable or disable the unsupported feature handler.
- DEBUG_SYSFONTS {0,1} = 0
  Whether to install a sysfont listener.\
""" % dict(py_exe=basename(sys.executable)),
    )
    subparsers = main_parser.add_subparsers(dest="subcommand")
    
    mod = None
    sc_name = (argv and argv[0]) or None
    if sc_name in (None, "-h", "--help"):
        main_parser.add_argument("-v", "--version", action="version", version="")
        for name, help in SubCommands.items():
            subparsers.add_parser(name, help=help)
    elif sc_name in ("-v", "--version"):
        main_parser.add_argument("-v", "--version", action="version", version=get_version())
    else:
        help = SubCommands[sc_name]
        # TODO use lazy dictionary (defaultdict) for imports
        mod = importlib.import_module(f"pypdfium2_cli.{sc_name.replace('-', '_')}")
        desc = getattr(mod, "PARSER_DESC", None)
        desc = (help + "\n\n" + desc) if desc else help
        subparser = subparsers.add_parser(
            sc_name, help=help, description=desc,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        mod.attach(subparser)
    
    return main_parser, mod


def api_main(argv=sys.argv[1:]):
    
    parser, mod = get_parser(argv)
    args = parser.parse_args(argv)
    
    if not args.subcommand:
        parser.print_help()
        return
    
    mod.main(args)


def cli_main():
    setup_logging()
    api_main()


if __name__ == "__main__":
    cli_main()
