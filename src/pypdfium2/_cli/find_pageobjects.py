# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os.path
from pypdfium2 import _namespace as pdfium
from pypdfium2._cli._parsers import pagetext_type
from pypdfium2._helpers._utils import (
    ObjtypeToConst,
    ObjtypeToName,
)


def attach_parser(subparsers):
    parser = subparsers.add_parser(
        "find-pageobjects",
        help = "Locate page objects of a certain type",
    )
    parser.add_argument(
        "input",
        type = os.path.abspath,
        help = "Path to the PDF document to work with",
    )
    parser.add_argument(
        "--password",
        help = "Password to unlock the PDF, if encrypted"
    )
    parser.add_argument(
        "--pages",
        type = pagetext_type,
        help = "The pages to search (defaults to all)",
    )
    parser.add_argument(
        "--types",
        nargs = "+",
        required = True,
        choices = [k for k in ObjtypeToConst.keys()],
        help = "Object types to consider",
    )


def main(args):
    
    doc = pdfium.PdfDocument(args.input, args.password)
    args.types = [ObjtypeToConst[t] for t in args.types]
    if args.pages is None:
        args.pages = [i for i in range(len(doc))]
    
    for index in args.pages:
        page = doc.get_page(index)
        for obj in page.get_objects():
            type = obj.get_type()
            if type in args.types:
                print(ObjtypeToName[type], obj.get_pos())
        page.close()
    
    doc.close()
