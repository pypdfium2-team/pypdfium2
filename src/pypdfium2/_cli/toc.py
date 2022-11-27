# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pypdfium2._cli._parsers import add_input, get_input


def attach(parser):
    add_input(parser, pages=False)
    parser.add_argument(
        "--max-depth",
        type = int,
        default = 15,
        help = "Maximum recursion depth to consider when parsing the table of contents",
    )


def main(args):
    pdf = get_input(args)
    toc = pdf.get_toc(
        max_depth = args.max_depth,
    )
    pdf.print_toc(toc)
