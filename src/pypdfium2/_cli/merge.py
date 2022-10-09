# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pypdfium2 import _namespace as pdfium


def _merge_files(input_paths, passwords):
    
    dest_pdf = pdfium.PdfDocument.new()
    index = 0
    
    for in_path, pwd in zip(input_paths, passwords):
        
        src_pdf = pdfium.PdfDocument(in_path, password=pwd)
        success = pdfium.FPDF_ImportPagesByIndex(dest_pdf.raw, src_pdf.raw, None, 0, index)
        if not success:
            raise RuntimeError("Importing pages failed.")
        
        index += len(src_pdf)
    
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
        "--passwords",
        nargs = "*",
        help = "A sequence of passwords to unlock encrypted PDFs. The value is ignored for non-encrypted documents, where any placeholder may be used.",
    )
    parser.add_argument(
        "--output", "-o",
        required = True,
        help = "Target path for the output document",
    )


def main(args):
    
    if not args.passwords:
        args.passwords = [None for _ in args.inputs]
    
    merged_pdf = _merge_files(args.inputs, args.passwords)
    with open(args.output, "wb") as buffer:
        merged_pdf.save(buffer)
