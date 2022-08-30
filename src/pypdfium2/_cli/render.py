# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import ast
from os.path import (
    join,
    abspath,
    basename,
    splitext,
)
from pypdfium2 import _namespace as pdfium
from pypdfium2._cli._parsers import pagetext_type


def rotation_type(string):
    rotation = int(string)
    if rotation not in (0, 90, 180, 270):
        raise ValueError("Invalid rotation value %s" % rotation)
    return rotation


def crop_type(string):
    crop = ast.literal_eval(string)
    if not isinstance(crop, (tuple, list)) or len(crop) != 4 or not all(isinstance(c, (int, float)) for c in crop):
        raise ValueError("Crop must be a list of four numbers.")
    return crop

ColourSchemeOpt = dict(
    default = None,
    metavar = "C",
    nargs = 4,
    type = int,
    help = "Option for rendering with custom colour scheme.",
)

def attach_parser(subparsers):
    parser = subparsers.add_parser(
        "render",
        help = "Rasterise pages of a PDF file",
    )
    parser.add_argument(
        "inputs",
        nargs = "+",
        help = "PDF documents to render",
    )
    parser.add_argument(
        "--passwords",
        nargs = "*",
        help = "A sequence of passwords to unlock encrypted PDFs. The value is ignored for non-encrypted documents, where any placeholder may be used.",
    )
    parser.add_argument(
        "--output", "-o",
        type = abspath,
        required = True,
        help = "Output directory where to place the serially numbered images",
    )
    parser.add_argument(
        "--format", "-f",
        default = "png",
        help = "File extension of the image format to use",
    )
    parser.add_argument(
        "--pages",
        default = None,
        type = pagetext_type,
        help = "Numbers of the pages to render (defaults to all)",
    )
    parser.add_argument(
        "--scale",
        default = 1,
        type = float,
        help = "Define the resolution of the output images. By default, one PDF point (1/72in) is rendered to 1x1 pixel. This factor scales the number of pixels that represent one point.",
    )
    parser.add_argument(
        "--rotation",
        default = 0,
        type = rotation_type,
        help = "Rotate pages by 90, 180 or 270 degrees",
    )
    parser.add_argument(
        "--background-colour",
        default = (255, 255, 255, 255),
        metavar = "C",
        nargs = 4,
        type = int,
        help = "Page background colour. It shall be given in RGBA format as a sequence of integers ranging from 0 to 255. Defaults to white.",
    )
    parser.add_argument(
        "--path-fill-colour",
        **ColourSchemeOpt
    )
    parser.add_argument(
        "--path-stroke-colour",
        **ColourSchemeOpt
    )
    parser.add_argument(
        "--text-fill-colour",
        **ColourSchemeOpt
    )
    parser.add_argument(
        "--text-stroke-colour",
        **ColourSchemeOpt
    )
    parser.add_argument(
        "--fill-to-stroke",
        action = "store_true",
        help = "Whether fill paths need to be stroked. Ignored if not rendering with custom colour scheme.",
    )
    parser.add_argument(
        "--force-halftone",
        action = "store_true",
        help = "Always use halftone for image stretching",
    )
    parser.add_argument(
        "--no-annotations",
        action = "store_true",
        help = "Prevent rendering of PDF annotations",
    )
    parser.add_argument(
        "--no-forms",
        action = "store_true",
        help = "Prevent rendering of PDF forms",
    )
    parser.add_argument(
        "--optimise-mode",
        default = pdfium.OptimiseMode.NONE,
        type = lambda string: pdfium.OptimiseMode[string.upper()],
        help = "Select a rendering optimisation mode (none, lcd_display, printing)",
    )
    parser.add_argument(
        "--greyscale",
        action = "store_true",
        help = "Whether to render in greyscale mode (no colours)",
    )
    parser.add_argument(
        "--crop",
        type = crop_type,
        default = (0, 0, 0, 0),
        help = "Amount to crop from (left, bottom, right, top)",
    )
    parser.add_argument(
        "--no-antialias",
        nargs = "+",
        default = (),
        choices = ("text", "image", "path"),
        help = "Item types that shall not be smoothed",
    )
    parser.add_argument(
        "--rev-byteorder",
        action = "store_true",
        help = "Render with reverse byte order internally, i. e. RGB(A) instead of BGR(A). The result should be completely identical.",
    )
    parser.add_argument(
        "--processes",
        default = os.cpu_count(),
        type = int,
        help = "The number of processes to use for rendering (defaults to the number of CPU cores)",
    )


def main(args):
    
    if not args.passwords:
        args.passwords = [None for _ in args.inputs]
    
    for input_path, password in zip(args.inputs, args.passwords):
        
        pdf = pdfium.PdfDocument(input_path, password=password)
        if args.pages:
            page_indices = args.pages
        else:
            page_indices = [i for i in range(len(pdf))]
        
        colour_scheme = None
        colour_scheme_kwargs = dict(
            path_fill = args.path_fill_colour,
            path_stroke = args.path_stroke_colour,
            text_fill = args.text_fill_colour,
            text_stroke = args.text_stroke_colour,
        )
        if any(colour_scheme_kwargs.values()):
            colour_scheme = pdfium.ColourScheme(**colour_scheme_kwargs)
        
        kwargs = dict(
            page_indices = page_indices,
            scale = args.scale,
            rotation = args.rotation,
            crop = args.crop,
            colour = args.background_colour,
            colour_scheme = colour_scheme,
            fill_to_stroke = args.fill_to_stroke,
            force_halftone = args.force_halftone,
            greyscale = args.greyscale,
            optimise_mode = args.optimise_mode,
            draw_annots = not args.no_annotations,
            draw_forms = not args.no_forms,
            rev_byteorder = args.rev_byteorder,
            n_processes = args.processes,
        )
        for type in args.no_antialias:
            kwargs["no_smooth%s" % type] = True
        
        renderer = pdf.render_topil(**kwargs)
        prefix = splitext(basename(input_path))[0] + "_"
        n_digits = len(str( max(page_indices)+1 ))
        
        for image, index in zip(renderer, page_indices):
            suffix = str(index+1).zfill(n_digits)
            output_path = "%s.%s" % (join(args.output, prefix+suffix), args.format)
            image.save(output_path)
            image.close()
        
        pdf.close()
