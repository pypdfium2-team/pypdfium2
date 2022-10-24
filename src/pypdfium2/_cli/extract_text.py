# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from enum import Enum
from pathlib import Path
from pypdfium2 import _namespace as pdfium
from pypdfium2._cli._parsers import parse_pagetext


class ExtractionStrategy (Enum):
    RANGE = 0
    BOUNDED = 1


def attach(parser):
    parser.add_argument(
        "input",
        type = Path,
        help = "Path of the input PDF",
    )
    parser.add_argument(
        "--password",
        help = "Password to unlock the PDF, if encrypted",
    )
    parser.add_argument(
        "--pages",
        help = "Page numbers to include (defaults to all)",
        type = parse_pagetext,
    )
    parser.add_argument(
        "--strategy",
        type = lambda s: ExtractionStrategy[s.upper()],
        default = ExtractionStrategy.RANGE,
        help = "PDFium text extraction strategy (range, bounded).",
        # TODO think out a strategy for choices (see https://github.com/python/cpython/issues/69247)
    )


def main(args):
    
    pdf = pdfium.PdfDocument(args.input, password=args.password)
    if args.pages is None:
        args.pages = [i for i in range(len(pdf))]
    
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
