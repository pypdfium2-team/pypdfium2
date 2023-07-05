# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i
# TODO? consider dotted access
from pypdfium2._cli._parsers import (
    add_input,
    add_n_digits,
    get_input,
    round_list,
)


def attach(parser):
    add_input(parser, pages=False)
    add_n_digits(parser)
    parser.add_argument(
        "--max-depth",
        type = int,
        default = 15,
        help = "Maximum recursion depth to consider when parsing the table of contents",
    )


def main(args):
    
    pdf = get_input(args)
    toc = pdf.get_toc(max_depth=args.max_depth)
    
    for bm in toc:
        count, dest = bm.get_count(), bm.get_dest()
        index, (view_mode, view_pos) = (dest.get_index(), dest.get_view()) if dest else (None, (pdfium_c.PDFDEST_VIEW_UNKNOWN_MODE, []))
        print(
            "    " * bm.level +
            "[%s] %s -> %s  # %s %s" % (
                "*" if count == 0 else f"{count}" if count < 0 else f"+{count}",
                bm.get_title(),
                index+1 if index is not None else "?",
                pdfium_i.ViewmodeToStr.get(view_mode),
                round_list(view_pos, args.n_digits),
            )
        )
