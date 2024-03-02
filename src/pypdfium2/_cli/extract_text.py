# SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# TODO? consider dotted access
from pypdfium2._cli._parsers import add_input, get_input

EXTRACT_RANGE   = "range"
EXTRACT_BOUNDED = "bounded"


def attach(parser):
    add_input(parser, pages=True)
    parser.add_argument(
        "--strategy",
        default = EXTRACT_RANGE,
        choices = (EXTRACT_RANGE, EXTRACT_BOUNDED),
        help = "PDFium text extraction strategy (range, bounded).",
    )


def main(args):
    
    pdf = get_input(args)
    
    sep = ""
    for i in args.pages:
        
        page = pdf[i]
        textpage = page.get_textpage()
        
        # TODO let caller pass in possible range/boundary parameters
        if args.strategy == EXTRACT_RANGE:
            text = textpage.get_text_range(force_this=True)
        elif args.strategy == EXTRACT_BOUNDED:
            text = textpage.get_text_bounded()
        else:
            assert False
        
        print(sep + f"# Page {i+1}\n" + text)
        sep = "\n"
