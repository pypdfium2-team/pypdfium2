# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from enum import Enum
from pypdfium2._cli._parsers import add_input, get_input


class ExtractionStrategy (Enum):
    RANGE = 0
    BOUNDED = 1


def attach(parser):
    add_input(parser, pages=True)
    parser.add_argument(
        "--strategy",
        type = lambda s: ExtractionStrategy[s.upper()],
        default = ExtractionStrategy.RANGE,
        help = "PDFium text extraction strategy (range, bounded).",
        # TODO think out a strategy for choices (see https://github.com/python/cpython/issues/69247)
    )


def main(args):
    
    pdf = get_input(args)
    
    sep = ""
    for i in args.pages:
        
        page = pdf.get_page(i)
        textpage = page.get_textpage()
        
        # TODO let caller pass in possible range/boundary parameters
        if args.strategy == ExtractionStrategy.RANGE:
            text = textpage.get_text_range()
        elif args.strategy == ExtractionStrategy.BOUNDED:
            text = textpage.get_text_bounded()
        else:
            assert False
        
        print(sep + "# Page %s\n" % (i+1) + text)
        sep = "\n"
