# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import argparse
import importlib
from os.path import basename
from pypdfium2._lazy import cached_property
from pypdfium2_cli._setup import setup_logging

class _InitClass:
    
    @cached_property
    def imports(self):
        global PYPDFIUM_INFO, PDFIUM_INFO, _libs
        from pypdfium2.version import PYPDFIUM_INFO, PDFIUM_INFO
        from pypdfium2_raw.bindings import _libs
        
        global SubCommands, CmdToModule
        SubCommands = {
            "arrange":        "Rearrange/merge documents",
            "attachments":    "List/extract/edit embedded files",
            "extract-images": "Extract images",
            "extract-text":   "Extract text",
            "imgtopdf":       "Convert images to PDF",
            "pageobjects":    "Print info on pageobjects",
            "pdfinfo":        "Print info on document and pages",
            "render":         "Rasterize pages",
            "tile":           "Tile pages (N-up)",
            "toc":            "Print table of contents",
        }
        CmdToModule = {n: importlib.import_module(f"pypdfium2_cli.{n.replace('-', '_')}") for n in SubCommands}

init = _InitClass()


def get_parser():
    
    main_parser = argparse.ArgumentParser(
        prog = "pypdfium2",
        formatter_class = argparse.RawTextHelpFormatter,
        description = """\
Command line interface to the pypdfium2 library (Python binding to PDFium)
Invoke as `pypdfium2` or `%(py_exe)s -m pypdfium2_cli`

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
    main_parser.add_argument(
        "--version", "-v",
        action = "version",
        version = f"pypdfium2 {PYPDFIUM_INFO}\n" f"pdfium {PDFIUM_INFO} at {_libs['pdfium']._name}"
    )
    subparsers = main_parser.add_subparsers(dest="subcommand")
    
    for name, help in SubCommands.items():
        mod = CmdToModule[name]
        desc = getattr(mod, "PARSER_DESC", None)
        desc = (help + "\n\n" + desc) if desc else help
        subparser = subparsers.add_parser(
            name, help=help, description=desc,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        mod.attach(subparser)
    
    return main_parser


def api_main(raw_args=sys.argv[1:]):
    
    init.imports
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
