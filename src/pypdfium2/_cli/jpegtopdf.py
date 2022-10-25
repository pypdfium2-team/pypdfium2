# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pathlib import Path
from pypdfium2 import _namespace as pdfium


def attach(parser):
    parser.add_argument(
        "images",
        nargs = "+",
        help = "Input JPEG images",
        type = Path,
    )
    parser.add_argument(
        "--output", "-o",
        required = True,
        type = Path,
        help = "Target path for the new PDF"
    )
    parser.add_argument(
        "--inline",
        action = "store_true",
        help = "Whether to load the image data into memory directly."
    )


def main(args):
    
    # Very rudimentary JPEG to PDF conversion, mostly for testing
    # The implementation could certainly be more sophisticated (e. g. configurable DPI, default DPI based on image metadata via Pillow, margins, crop, positioning, ...)
    
    pdf = pdfium.PdfDocument.new()
    
    for path in args.images:
        
        # Simple check if the input files are JPEGs - a better implementation could use mimetypes or python-magic instead
        assert path.suffix.lower() in (".jpg", ".jpeg")
        
        image = pdfium.PdfImage.new(pdf)
        buffer = open(path, "rb")
        image.load_jpeg(buffer, inline=args.inline, autoclose=True)
        width, height = image.get_size()
        
        matrix = pdfium.PdfMatrix()
        matrix.scale(width, height)
        image.set_matrix(matrix)
        
        page = pdf.new_page(width, height)
        page.insert_object(image)
        page.generate_content()
    
    if args.output.exists():
        raise FileExistsError(args.output)
    
    with open(args.output, "wb") as buffer:
        pdf.save(buffer)
