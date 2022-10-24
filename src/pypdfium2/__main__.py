# PYTHON_ARGCOMPLETE_OK
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import logging
import argparse
import importlib
from pypdfium2.version import (
    V_PYPDFIUM2,
    V_LIBPDFIUM,
    IS_SOURCEBUILD,
)

try:
    import argcomplete
except ImportError:
    argcomplete = None


SubCommands = {
    "render":
        "Rasterise PDF pages",
    "toc":
        "Show PDF table of contents",
    "merge":
        "Concatenate PDFs",
    "tile":
        "Perform page tiling (N-up)",
    "extract-text":
        "Extract text from PDF pages",
    "extract-images":
        "Extract images from PDF pages (lossy)",
    "find-objects":
        "Locate page objects",
    "jpegtopdf":
        "Convert JPEG images to PDF",
}

def _load_modules():
    modules = {}
    for name in SubCommands.keys():
        mod_path = "pypdfium2._cli.%s" % name.replace("-", "_")
        modules[name] = importlib.import_module(mod_path)
    return modules

CmdToModule = _load_modules()


def get_parser():
    
    main_parser = argparse.ArgumentParser(
        prog = "pypdfium2",
        description = "Command line interface to the pypdfium2 library (Python binding to PDFium)",
    )
    main_parser.add_argument(
        "--version", "-v",
        action = "version",
        version = "pypdfium2 %s (libpdfium %s, %s build)" % (
            V_PYPDFIUM2, V_LIBPDFIUM,
            "custom" if IS_SOURCEBUILD else "pdfium-binaries",
        ),
    )
    subparsers = main_parser.add_subparsers(dest="subcommand")
    
    for name, help in SubCommands.items():
        subparser = subparsers.add_parser(
            name, description=help, help=help,
        )
        module = CmdToModule[name]
        module.attach(subparser)
    
    if argcomplete is not None:
        argcomplete.autocomplete(main_parser)
    
    return main_parser


def main(raw_args=sys.argv[1:]):
    
    lib_logger = logging.getLogger("pypdfium2")
    lib_logger.addHandler(logging.StreamHandler())
    lib_logger.setLevel(logging.DEBUG)
    
    parser = get_parser()
    args = parser.parse_args(raw_args)
    if not args.subcommand:
        parser.print_help()
        return
    
    module = CmdToModule[args.subcommand]
    module.main(args)


if __name__ == "__main__":
    main()
