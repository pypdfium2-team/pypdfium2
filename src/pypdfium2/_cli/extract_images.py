# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pathlib import Path
from pypdfium2 import _namespace as pdfium
from pypdfium2._cli._parsers import parse_pagetext


def attach(parser):
    parser.add_argument(
        "input",
        type = Path,
        help = "Path of the input PDF",
    )
    parser.add_argument(
        "--output-dir", "-o",
        required = True,
        type = Path,
        help = "Output directory to take the extracted images",
    )
    parser.add_argument(
        "--format",
        default = "jpg",
        help = "Image format to use when saving the bitmaps",
    )
    parser.add_argument(
        "--password",
        help = "Password to unlock the PDF, if encrypted",
    )
    parser.add_argument(
        "--pages",
        help = "Page numbers to include (defaults to all)",
        type = parse_pagetext,
    )
    parser.add_argument(
        "--render",
        action = "store_true",
        help = "Whether to get rendered bitmaps, taking masks and transform matrices into account.",
    )
    parser.add_argument(
        "--max-depth",
        type = int,
        default = 2,
        help = "Maximum recursion depth to consider when looking for page objects.",
    )


def main(args):
    
    pdf = pdfium.PdfDocument(args.input, password=args.password)
    if args.pages is None:
        args.pages = [i for i in range(len(pdf))]
    
    if not args.output_dir.is_dir():
        raise NotADirectoryError(args.output_dir)
    
    image_objs = []
    for i in args.pages:
        page = pdf.get_page(i)
        obj_searcher = page.get_objects(max_depth=args.max_depth)
        image_objs += [obj for obj in obj_searcher if isinstance(obj, pdfium.PdfImage)]
    
    n_digits = len(str(len(image_objs)))
    for i, obj in enumerate(image_objs):
        pil_image = obj.get_bitmap(render=args.render).to_pil()
        output_path = args.output_dir / ("%s_%0*d.%s" % (args.input.stem, n_digits, i+1, args.format))
        pil_image.save(output_path)
