# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pypdfium2._helpers._internal import consts
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
    toc = pdf.get_toc(
        max_depth = args.max_depth,
    )
    
    for item in toc:
        
        if item.n_kids == 0:
            state = "*"
        elif item.is_closed:
            state = "-"
        else:
            state = "+"
        
        if item.page_index is None:
            target = "?"
        else:
            target = item.page_index + 1
        
        print(
            "    " * item.level +
            "[%s] %s -> %s  # %s %s" % (
                state, item.title, target,
                consts.ViewmodeToStr.get(item.view_mode),
                round_list(item.view_pos, args.n_digits),
            )
        )
