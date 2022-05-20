# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os.path
from pypdfium2 import _namespace as pdfium
from pypdfium2._cli._parsers import pagetext_type


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
        "--left",
        type = int,
        default = 0,
        help = "Left coordinate of the area to search for text.",
    )
    parser.add_argument(
        "--bottom",
        type = int,
        default = 0,
        help = "Bottom coordinate of the area to search for text.",
    )
    parser.add_argument(
        "--right",
        type = int,
        default = 0,
        help = "Right coordinate of the area to search for text.",
    )
    parser.add_argument(
        "--top",
        type = int,
        default = 0,
        help = "Top coordinate of the area to search for text.",
    )


def main(args):
    
    doc = pdfium.PdfDocument(args.input, args.password)
    if args.pages is None:
        args.pages = [i for i in range(len(doc))]
    
    sep = ''
    for index in args.pages:
        textpage = doc.get_textpage(index)
        text = textpage.get_text(
            left = args.left,
            bottom = args.bottom,
            right = args.right,
            top = args.top,
        )
        textpage.close()
        print(sep + "# Page %s\n" % (index+1) + text)
        sep = '\n'
    
    doc.close()
