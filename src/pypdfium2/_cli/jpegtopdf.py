# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os.path
from pypdfium2 import _namespace as pdfium


def attach_parser(subparsers):
    parser = subparsers.add_parser(
        "jpegtopdf",
        help = "Convert JPEG images to PDF",
    )
    parser.add_argument(
        "images",
        nargs = "+",
        help = "Input JPEG images",
        type = os.path.abspath,
    )
    parser.add_argument(
        "--output", "-o",
        required = True,
        help = "Target path for the new PDF"
    )
    parser.add_argument(
        "--inline",
        action = "store_true",
        help = "Whether to use FPDFImageObj_LoadJpegFileInline() rather than FPDFImageObj_LoadJpegFile()."
    )


def main(args):
    
    # Very rudimentary JPEG to PDF conversion, mostly for testing
    # The implementation could certainly be more sophisticated (e. g. configurable DPI, default DPI based on image metadata via Pillow, margins, crop, positioning, ...)
    
    pdf = pdfium.PdfDocument.new()
    
    for file in args.images:
        
        # Simple check if the input files are actually JPEGs
        # A better implementation could use mimetypes or python-magic instead
        assert any(file.lower().endswith(ext) for ext in (".jpg", ".jpeg"))
        
        image = pdfium.PdfImageObject.new(pdf)
        
        buffer = open(file, "rb")
        width, height = image.load_jpeg(buffer, inline=args.inline, autoclose=True)
        
        page = pdf.new_page(width, height)
        page.insert_object(image)
        page.generate_content()
    
    if os.path.exists(args.output):
        raise FileExistsError("Refusing to overwrite '%s'" % args.output)
    
    with open(args.output, "wb") as buffer:
        pdf.save(buffer)
