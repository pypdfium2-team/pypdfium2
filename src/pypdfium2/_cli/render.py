# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
from os.path import (
    join,
    abspath,
    basename,
    splitext,
)
from pypdfium2 import _namespace as pdfium
from pypdfium2._cli._parsers import pagetext_type


ColourOpts = dict(
    metavar = "C",
    nargs = 4,
    type = int,
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
        default = "jpg",
        help = "The image format to use",
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
        type = int,
        choices = (0, 90, 180, 270),
        help = "Rotate pages by 90, 180 or 270 degrees",
    )
    parser.add_argument(
        "--fill-colour",
        default = (255, 255, 255, 255),
        help = "Colour the bitmap will be filled with before rendering. It shall be given in RGBA format as a sequence of integers ranging from 0 to 255. Defaults to white.",
        **ColourOpts,
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
        nargs = 4,
        type = float,
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
        "--prefer-bgrx",
        action = "store_true",
        help = "Request the use of a four-channel pixel format for coloured output, even if rendering without transparency.",
    )
    parser.add_argument(
        "--processes",
        default = os.cpu_count(),
        type = int,
        help = "The number of processes to use for rendering (defaults to the number of CPU cores)",
    )
    
    colour_scheme = parser.add_argument_group(
        title = "Colour scheme",
        description = "Options for rendering with custom colour scheme",
    )
    colour_scheme.add_argument(
        "--path-fill",
        **ColourOpts
    )
    colour_scheme.add_argument(
        "--path-stroke",
        **ColourOpts
    )
    colour_scheme.add_argument(
        "--text-fill",
        **ColourOpts
    )
    colour_scheme.add_argument(
        "--text-stroke",
        **ColourOpts
    )
    colour_scheme.add_argument(
        "--fill-to-stroke",
        action = "store_true",
        help = "Whether fill paths need to be stroked.",
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
        
        cs_kwargs = dict(
            path_fill = args.path_fill,
            path_stroke = args.path_stroke,
            text_fill = args.text_fill,
            text_stroke = args.text_stroke,
        )
        cs = None
        if all(cs_kwargs.values()):
            cs = pdfium.ColourScheme(
                fill_to_stroke = args.fill_to_stroke,
                **cs_kwargs,
            )
        elif any(cs_kwargs.values()):
            raise ValueError("If rendering with custom colour scheme, all parameters need to be set explicitly.")
        
        kwargs = dict(
            page_indices = page_indices,
            n_processes = args.processes,
            scale = args.scale,
            rotation = args.rotation,
            crop = args.crop,
            greyscale = args.greyscale,
            fill_colour = args.fill_colour,
            colour_scheme = cs,
            optimise_mode = args.optimise_mode,
            draw_annots = not args.no_annotations,
            draw_forms = not args.no_forms,
            force_halftone = args.force_halftone,
            rev_byteorder = args.rev_byteorder,
            prefer_bgrx = args.prefer_bgrx,
        )
        for type in args.no_antialias:
            kwargs["no_smooth%s" % type] = True
        
        prefix = splitext(basename(input_path))[0] + "_"
        n_digits = len(str( max(page_indices)+1 ))
        renderer = pdf.render_to(pdfium.BitmapConv.pil_image, **kwargs)
        
        for image, index in zip(renderer, page_indices):
            suffix = str(index+1).zfill(n_digits)
            output_path = "%s.%s" % (join(args.output, prefix+suffix), args.format)
            image.save(output_path)
