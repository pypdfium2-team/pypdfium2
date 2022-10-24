# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pathlib import Path
from pypdfium2 import _namespace as pdfium
from pypdfium2._cli._parsers import parse_pagetext


def attach(parser):
    
    obj_types = list( pdfium.ObjectTypeToConst.keys() )
    
    parser.add_argument(
        "input",
        type = Path,
        help = "Path to the PDF document to work with.",
    )
    parser.add_argument(
        "--password",
        help = "Password to unlock the PDF, if encrypted."
    )
    parser.add_argument(
        "--pages",
        type = parse_pagetext,
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
    
    pdf = pdfium.PdfDocument(args.input, password=args.password)
    args.types = [pdfium.ObjectTypeToConst[t] for t in args.types]
    if args.pages is None:
        args.pages = [i for i in range(len(pdf))]
    
    # TODO add option to show image metadata; print count of found objects at end
    
    for i in args.pages:
        
        page = pdf.get_page(i)
        obj_searcher = page.get_objects(max_depth=args.max_depth)
        
        for obj in obj_searcher:
            if obj.type not in args.types:
                continue
            print("    "*obj.level + pdfium.ObjectTypeToStr[obj.type], obj.get_pos())
