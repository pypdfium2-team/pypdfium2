# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2.internal as pdfium_i
from pypdfium2_cli._parsers import (
    add_input, add_n_digits,
    get_input, round_list,
)
from pypdfium2_cfg.stl import BooleanOptionalAction
from pypdfium2 import PDFIUM_INFO, PdfBookmark, PdfBookmarkStyle


def attach(parser):
    add_input(parser, pages=False)
    add_n_digits(parser)
    parser.add_argument(
        "--max-depth",
        type = int,
        default = 15,
        help = "Maximum recursion depth to consider when parsing the table of contents",
    )
    parser.add_argument(
        "--highlight",
        action = BooleanOptionalAction,
        default = True,
        help = "Whether console ANSI escape sequences may be used to indicate color/style. Defauls to true.",
    )


class ColorIndicator:
    
    def __init__(self, indicator, sep):
        self.indicator = indicator
        self.sep = sep
    
    def __call__(self, color):
        r, g, b = tuple(round(c*255) for c in color)
        return f"\x1b[38;2;{r};{g};{b}m" + self.indicator + "\x1b[0m" + self.sep
    
    @staticmethod
    def noop(color):
        return ""


_NO_STYLE = PdfBookmarkStyle(0)
if PDFIUM_INFO.build > 8031:
    get_style = PdfBookmark.get_style
else:
    def get_style(bm):
        return _NO_STYLE


def main(args):
    
    pdf = get_input(args)
    if args.highlight:
        icol = ColorIndicator("⬤", sep=" ")
    else:
        icol = ColorIndicator.noop
    
    for bm in pdf.get_toc(max_depth=args.max_depth):
        
        title = bm.get_title()
        color = bm.get_color()
        style = get_style(bm)
        count = bm.get_count()
        count_str = f"{count:+}" if count != 0 else "*"
        out = "    " * bm.level
        # unconditionally add "->" regardless of whether a dest follows or not, to avoid ambiguity with titles potentially containing the same
        out += "[%s] %s -> " % (count_str, title)
        
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
        
        extras = []
        if style:
            extras.append(style.name.replace("|","+").lower())
        if color:
            extras.append(icol(color) + f"RGB{round_list(color, args.n_digits)}")
        if extras:
            out += " | " + ", ".join(extras)
        
        print(out)
