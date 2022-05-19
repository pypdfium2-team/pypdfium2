# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os.path
from pypdfium2 import _namespace as pdfium
from pypdfium2._cli._parsers import pagetext_type


NameToObjtype = dict(
    unknown = pdfium.FPDF_PAGEOBJ_UNKNOWN,
    text    = pdfium.FPDF_PAGEOBJ_TEXT,
    path    = pdfium.FPDF_PAGEOBJ_PATH,
    image   = pdfium.FPDF_PAGEOBJ_IMAGE,
    shading = pdfium.FPDF_PAGEOBJ_SHADING,
    form    = pdfium.FPDF_PAGEOBJ_FORM,
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
        "--type",
        required = True,
        choices = [k for k in NameToObjtype.keys()],
        help = "Object types to consider",
    )


def main(args):
    
    doc = pdfium.PdfDocument(args.input, args.password)
    args.type = NameToObjtype[args.type]
    if args.pages is None:
        args.pages = [i for i in range(len(doc))]
    
    for index in args.pages:
        page = doc.get_page(index)
        pageobjs = pdfium.get_pageobjs(page)
        for obj in pdfium.filter_pageobjs(pageobjs, args.type):
            print( pdfium.locate_pageobj(obj) )
        pdfium.close_page(page)
    
    doc.close()
