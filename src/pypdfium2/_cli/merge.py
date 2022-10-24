# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pypdfium2 import _namespace as pdfium


def attach(parser):
    parser.add_argument(
        "inputs",
        nargs = "+",
        help = "A sequence of PDF files to concatenate",
    )
    parser.add_argument(
        "--passwords",
        nargs = "*",
        help = "A sequence of passwords to unlock encrypted PDFs. Any placeholder may be used for non-encrypted documents.",
    )
    parser.add_argument(
        "--output", "-o",
        required = True,
        help = "Target path for the output document",
    )


def main(args):
    
    if not args.passwords:
        args.passwords = [None for _ in args.inputs]
    
    dest_pdf = pdfium.PdfDocument.new()
    index = 0
    for in_path, password in zip(args.inputs, args.passwords):
        src_pdf = pdfium.PdfDocument(in_path, password=password)
        dest_pdf.import_pages(src_pdf)
        index += len(src_pdf)
    
    with open(args.output, "wb") as buffer:
        dest_pdf.save(buffer)
