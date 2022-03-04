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

def print_toc(toc):
    for item in toc:
        print(
            '    ' * item.level +
            '{} -> {}  # {} {}'.format(
                item.title,
                item.page_index + 1,
                item.view_mode,
                item.view_pos,
            )
        )


def main(argv, prog, desc):
    args = parse_args(argv, prog, desc)
    doc = pdfium.PdfDocument(args.input)
    print_toc( doc.get_toc() )
    doc.close()
