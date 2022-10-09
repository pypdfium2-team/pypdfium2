# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os.path
from pypdfium2 import _namespace as pdfium
from pypdfium2._cli._parsers import pagetext_type


STRATEGY_RANGE = "range"
STRATEGY_BOUNDED = "bounded"


def attach_parser(subparsers):
    parser = subparsers.add_parser(
        "extract-text",
        help = "Extract text from a PDF page in given boundaries",
    )
    parser.add_argument(
        "input",
        type = os.path.abspath,
        help = "Path to the PDF document to work with",
    )
    parser.add_argument(
        "--password",
        help = "Password to unlock the PDF, if encrypted",
    )
    parser.add_argument(
        "--pages",
        help = "Page numbers to include (defaults to all)",
        type = pagetext_type,
    )
    parser.add_argument(
        "--strategy",
        type = str,
        choices = (STRATEGY_RANGE, STRATEGY_BOUNDED),
        default = STRATEGY_RANGE,
        help = "PDFium text extraction strategy.",
    )


def main(args):
    
    doc = pdfium.PdfDocument(args.input, password=args.password)
    if args.pages is None:
        args.pages = [i for i in range(len(doc))]
    
    sep = ""
    for index in args.pages:
        
        page = doc.get_page(index)
        textpage = page.get_textpage()
        
        # TODO let caller pass in possible range/boundary parameters
        if args.strategy == STRATEGY_RANGE:
            text = textpage.get_text_range()
        elif args.strategy == STRATEGY_BOUNDED:
            text = textpage.get_text_bounded()
        else:
            assert False
        
        print(sep + "# Page %s\n" % (index+1) + text)
        sep = "\n"
