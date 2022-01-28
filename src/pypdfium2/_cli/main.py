# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
from pypdfium2._version import (
    V_PYPDFIUM2,
    V_LIBPDFIUM,
)
from pypdfium2._cli._parser import CliRunner
from pypdfium2._cli import (
    renderer,
    toc,
    merger,
    tiler,
)


def main(argv=sys.argv[1:]):
    
    runner = CliRunner(
        program = "PyPDFium2",
        version = "{} (libpdfium {})".format(V_PYPDFIUM2, V_LIBPDFIUM),
        description = "Command line interface to the PyPDFium2 Python library",
        argv = argv,
    )
    
    runner.add_subcommand(
        "render",
        method = renderer.main,
        help = "Rasteries pages of a PDF file",
    )
    runner.add_subcommand(
        "toc",
        method = toc.main,
        help = "Show the table of contents for a PDF document",
    )
    runner.add_subcommand(
        "merge",
        method = merger.main,
        help = "Concatenate PDF files",
    )
    runner.add_subcommand(
        "tile",
        method = tiler.main,
        help = "Perform page tiling (N-up compositing)",
    )
    
    runner.run()
