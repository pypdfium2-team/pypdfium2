#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0

import ctypes
import argparse
import pypdfium2 as pdfium


def _merge_pdfs(input_paths):
    
    dest_doc = pdfium.FPDF_CreateNewDocument()
    
    for in_path in reversed(input_paths):
        with pdfium.PdfContext(in_path) as src_doc:
            page_count = pdfium.FPDF_GetPageCount(src_doc)
            page_indices = (ctypes.c_int * page_count)(*[i for i in range(page_count)])
            pdfium.FPDF_ImportPagesByIndex(dest_doc, src_doc, page_indices, page_count, 0)
    
    return dest_doc


def parse_args():
    parser = argparse.ArgumentParser(
        description = "Merge PDF files with PyPDFium2.",
    )
    parser.add_argument(
        'input_paths',
        nargs = '+',
    )
    parser.add_argument(
        '--output-path', '-o',
        required = True,
    )
    return parser.parse_args()


def main(input_paths, output_path):
    merged_doc = _merge_pdfs(input_paths)
    with open(output_path, 'wb') as file_handle:
        pdfium.save_pdf(merged_doc, file_handle)
    

if __name__ == '__main__':
    args = parse_args()
    main(
        input_paths = args.input_paths,
        output_path = args.output_path,
    )
