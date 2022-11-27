# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import traceback
from pathlib import Path
import pypdfium2.raw as pdfium_c
import pypdfium2._helpers as pdfium
from pypdfium2._cli._parsers import add_input, get_input


def attach(parser):
    add_input(parser, pages=True)
    parser.add_argument(
        "--output-dir", "-o",
        required = True,
        type = Path,
        help = "Output directory to take the extracted images",
    )
    parser.add_argument(
        "--max-depth",
        type = int,
        default = 2,
        help = "Maximum recursion depth to consider when looking for page objects.",
    )
    parser.add_argument(
        "--use-bitmap",
        action = "store_true",
        help = "Enforce the use of bitmaps rather than attempting a smart extraction of the image.",
    )
    parser.add_argument(
        "--format",
        help = "Image format to use when saving bitmaps. (Fallback if doing smart extraction.)",
    )
    parser.add_argument(
        "--render",
        action = "store_true",
        help = "Whether to get rendered bitmaps, taking masks and transform matrices into account. (Fallback if doing smart extraction.)",
    )


def main(args):
    
    if not args.output_dir.is_dir():
        raise NotADirectoryError(args.output_dir)
    if args.use_bitmap and not args.format:
        args.format = "png"
    
    pdf = get_input(args)
    
    images = []
    for i in args.pages:
        page = pdf.get_page(i)
        obj_searcher = page.get_objects(
            filter = (pdfium_c.FPDF_PAGEOBJ_IMAGE, ),
            max_depth = args.max_depth,
        )
        images += list(obj_searcher)
    
    n_digits = len(str(len(images)))
    
    for i, image in enumerate(images):
        prefix = args.output_dir / ("%s_%0*d" % (args.input.stem, n_digits, i+1))
        
        try:
            if args.use_bitmap:
                pil_image = image.get_bitmap(render=args.render).to_pil()
                pil_image.save("%s.%s" % (prefix, args.format))
            else:
                image.extract(prefix, fb_format=args.format, fb_render=args.render)
        except pdfium.PdfiumError:
            traceback.print_exc()
