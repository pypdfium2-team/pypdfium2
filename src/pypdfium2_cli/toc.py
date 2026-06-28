# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2._helpers as pdfium
import pypdfium2.internal as pdfium_i
from pypdfium2_cli._parsers import (
    add_input, add_n_digits,
    get_input, round_list,
    BooleanOptionalAction,
)
from pypdfium2.version import PDFIUM_INFO


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
        "--color-indicator",
        action = BooleanOptionalAction,
        default = True,
        help = "Whether to add a color indicator to bookmarks that declare a color. The indicator is a Unicode symbol wrapped in an ANSI escape sequence. Default is enabled.",
    )


class ColorIndicator:
    
    def __init__(self, enable, indicator, sep):
        self.get = self._impl if enable else self._noop
        self.indicator = indicator
        self.sep = sep
    
    def _impl(self, color):
        r, g, b = tuple(round(c*255) for c in color)
        return f"\x1b[38;2;{r};{g};{b}m" + self.indicator + "\x1b[0m" + self.sep
    
    def _noop(self, color):
        return ""


if PDFIUM_INFO.build > 7912:
    get_color = pdfium.PdfBookmark.get_color
else:
    def get_color(bm):
        return None

def main(args):
    
    pdf = get_input(args)
    icol = ColorIndicator(args.color_indicator, "⬤", sep=" ").get
    
    for bm in pdf.get_toc(max_depth=args.max_depth):
        
        title = bm.get_title()
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
        
        color = get_color(bm)
        if color:
            out += " | " + icol(color) + f"RGB{round_list(color, args.n_digits)}"
        
        print(out)
