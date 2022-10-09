# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os.path
from pypdfium2 import _namespace as pdfium
from pypdfium2._cli._parsers import pagetext_type


def attach_parser(subparsers):
    obj_types = list(pdfium.ObjectTypeToConst.keys())
    parser = subparsers.add_parser(
        "find-pageobjects",
        help = "Locate page objects of given types.",
    )
    parser.add_argument(
        "input",
        type = os.path.abspath,
        help = "Path to the PDF document to work with.",
    )
    parser.add_argument(
        "--password",
        help = "Password to unlock the PDF, if encrypted."
    )
    parser.add_argument(
        "--pages",
        type = pagetext_type,
        help = "The pages to search (defaults to all).",
    )
    parser.add_argument(
        "--types",
        nargs = "+",
        metavar = "T",
        choices = obj_types,
        default = obj_types,
        help = "Object types to consider (defaults to all). Choices: %s" % obj_types,
    )
    parser.add_argument(
        "--max-depth",
        type = int,
        default = 2,
        help = "Maximum recursion depth to consider when descending into Form XObjects.",
    )


def main(args):
    
    doc = pdfium.PdfDocument(args.input, password=args.password)
    args.types = [pdfium.ObjectTypeToConst[t] for t in args.types]
    if args.pages is None:
        args.pages = [i for i in range(len(doc))]
    
    for index in args.pages:
        page = doc.get_page(index)
        for obj in page.get_objects(max_depth=args.max_depth):
            if obj.type in args.types:
                print("    "*obj.level + pdfium.ObjectTypeToStr[obj.type], obj.get_pos())
