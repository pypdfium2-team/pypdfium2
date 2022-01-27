# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
from pypdfium2 import _namespace as pdfium
from pypdfium2._cli._parser import ArgParser


def _merge_pdfs(input_paths):
    
    dest_doc = pdfium.FPDF_CreateNewDocument()
    
    for in_path in reversed(input_paths):
        with pdfium.PdfContext(in_path) as src_doc:
            page_count = pdfium.FPDF_GetPageCount(src_doc)
            page_indices = (ctypes.c_int * page_count)(*[i for i in range(page_count)])
            pdfium.FPDF_ImportPagesByIndex(dest_doc, src_doc, page_indices, page_count, 0)
    
    return dest_doc


def parse_args(argv, prog, desc):
    
    parser = ArgParser(
        prog = prog,
        description = desc,
    )
    
    parser.add_argument(
        'inputs',
        nargs = '+',
        help = "A sequence of PDF files to concatenate",
    )
    parser.add_argument(
        '--output', '-o',
        required = True,
        help = "Target path for the output document",
    )
    
    return parser.parse_args(argv)


def main(argv, prog, desc):
    
    args = parse_args(argv, prog, desc)
    merged_doc = _merge_pdfs(args.inputs)
    
    with open(args.output, 'wb') as file_handle:
        pdfium.save_pdf(merged_doc, file_handle)
