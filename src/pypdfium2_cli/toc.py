# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2.internal as pdfium_i
from pypdfium2_cli._parsers import (
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
        
        # unconditionally add "->" to avoid ambiguity with titles potentially containing the same
        count = bm.get_count()
        count_str = f"{count:+}" if count != 0 else "*"
        out = "    " * bm.level
        out += "[%s] %s -> " % (count_str, bm.get_title())
        
        dest = bm.get_dest()
        if dest:
            index = dest.get_index()
            view_mode, view_pos = dest.get_view()
            out += "%s  # %s %s" % (
                index+1 if index != None else "?",
                pdfium_i.ViewmodeToStr.get(view_mode),
                round_list(view_pos, args.n_digits),
            )
        else:
            out += "_"
        
        color = bm.get_color()
        if color:
            color = round_list(color, args.n_digits)
            out += f" | RGB{color}"
        
        print(out)
