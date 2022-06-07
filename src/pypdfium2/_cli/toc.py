# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pypdfium2 import _namespace as pdfium


def attach_parser(subparsers):
    parser = subparsers.add_parser(
        "toc",
        help = "Show a PDF document's table of contents",
    )
    parser.add_argument(
        "input",
        help = "PDF document of which to print the outline",
    )
    parser.add_argument(
        "--max-depth",
        type = int,
        default = 15,
        help = "Maximum recursion depth to consider when parsing the table of contents",
    )


def main(args):
    pdf = pdfium.PdfDocument(args.input)
    pdf.print_toc( pdf.get_toc() )
    pdf.close()
