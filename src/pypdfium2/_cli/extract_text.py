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


def main(args):
    
    doc = pdfium.PdfDocument(args.input, args.password)
    if args.pages is None:
        args.pages = [i for i in range(len(doc))]
    
    sep = ""
    for index in args.pages:
        
        page = doc.get_page(index)
        textpage = page.get_textpage()
        text = textpage.get_text()
        
        [g.close() for g in (textpage, page)]
        
        print(sep + "# Page %s\n" % (index+1) + text)
        sep = "\n"
    
    doc.close()
