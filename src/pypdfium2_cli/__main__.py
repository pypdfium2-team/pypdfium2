# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Important: Do not import from the core `pypdfium2` module here, since it initializes the library, which shall be deferred until after setup_logging().
# Other modules can be imported as long as they don't import from `pypdfium2` in turn.

import sys
import argparse
from os.path import basename
from importlib import import_module
from pypdfium2_cli._setup import (
    setup_logging, keydefaultdict, cached_property,
)

ModuleLoader = keydefaultdict(import_module)

class _LocalLazyClass:
    @cached_property
    def version_str(self):
        from pypdfium2.version import PYPDFIUM_INFO, PDFIUM_INFO
        from pypdfium2_raw.bindings import _libs
        return f"pypdfium2 {PYPDFIUM_INFO}\npdfium {PDFIUM_INFO} at {_libs['pdfium']._name}"

LocalLazy = _LocalLazyClass()

SubCommands = {
    "arrange":        "Rearrange/merge documents",
    "attachments":    "List/extract/edit embedded files",
    "extract-images": "Extract images",
    "extract-text":   "Extract text",
    "imgtopdf":       "Convert images to PDF",
    "pageobjects":    "Print info on pageobjects",
    "pdfinfo":        "Print info on document and pages",
    "fonts":          "List a document's fonts",
    "default-fonts":  "Dump info about default fonts",
    "render":         "Rasterize pages",
    "tile":           "Tile pages (N-up)",
    "toc":            "Print table of contents",
}


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
- DEBUG_AUTOCLOSE {debug,warning,critical} = warning
  How much info to print about (auto-)closing of PDFium objects.
- DEBUG_UNSUPPORTED {0,1} = 1
  Whether to enable or disable the unsupported feature handler.
- DEBUG_SYSFONTS {0,1} = 0
  Whether to install a sysfont listener.\
""" % dict(py_exe=basename(sys.executable)),
    )
    main_parser.add_argument(
        "-v", "--version",
        action = "version",
        version = LocalLazy.version_str,
    )
    subparsers = main_parser.add_subparsers(dest="subcommand")
    
    mod = None
    sc_name = (argv and argv[0]) or None
    other_scs = SubCommands.copy()
    
    if sc_name in SubCommands:
        del other_scs[sc_name]
        mod = ModuleLoader[f"pypdfium2_cli.{sc_name.replace('-', '_')}"]
        help = SubCommands[sc_name]
        desc = getattr(mod, "PARSER_DESC", None)
        desc = (help + "\n\n" + desc) if desc else help
        subparser = subparsers.add_parser(
            sc_name, help=help, description=desc,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        mod.attach(subparser)
    
    for name, help in other_scs.items():
        subparsers.add_parser(name, help=help)
    
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
