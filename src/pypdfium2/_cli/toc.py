# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pypdfium2 import _namespace as pdfium
from pypdfium2._cli._parser import ArgParser


def parse_args(argv, prog, desc):
    parser = ArgParser(
        prog = prog,
        description = desc,
    )
    parser.add_argument(
        'input',
        help = "PDF document of which to print the outline",
    )
    parser.add_argument(
        '--max-depth',
        type = int,
        default = 15,
        help = "Maximum recursion depth to consider when parsing the table of contents",
    )
    return parser.parse_args(argv)


def main(argv, prog, desc):
    
    args = parse_args(argv, prog, desc)
    
    with pdfium.PdfContext(args.input) as pdf:
        pdfium.print_toc( pdfium.get_toc(pdf, max_depth=args.max_depth) )
