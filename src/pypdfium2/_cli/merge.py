# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
from pypdfium2 import _namespace as pdfium


def _merge_files(input_paths):
    
    dest_pdf = pdfium.PdfDocument.new()
    
    for in_path in reversed(input_paths):
        src_pdf = pdfium.PdfDocument(in_path)
        n_pages = len(src_pdf)
        page_indices = (ctypes.c_int * n_pages)(*[i for i in range(n_pages)])
        pdfium.FPDF_ImportPagesByIndex(dest_pdf.raw, src_pdf.raw, page_indices, n_pages, 0)
        src_pdf.close()
    
    return dest_pdf


def attach_parser(subparsers):
    parser = subparsers.add_parser(
        "merge",
        help = "Concatenate PDF files",
    )
    parser.add_argument(
        "inputs",
        nargs = "+",
        help = "A sequence of PDF files to concatenate",
    )
    parser.add_argument(
        "--output", "-o",
        required = True,
        help = "Target path for the output document",
    )


def main(args):
    merged_pdf = _merge_files(args.inputs)
    with open(args.output, 'wb') as buffer:
        merged_pdf.save(buffer)
    merged_pdf.close()
