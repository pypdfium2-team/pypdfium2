# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import PIL.Image
from os.path import (
    join,
    abspath,
    basename,
    splitext,
)
from pypdfium2 import _namespace as pdfium
from pypdfium2._helpers._utils import UnreverseBitmapStr
from pypdfium2._cli._parsers import pagetext_type


def rotation_type(string):
    rotation = int(string)
    if rotation not in (0, 90, 180, 270):
        raise ValueError("Invalid rotation value %s" % rotation)
    return rotation


ColorSchemeOpt = dict(
    default = None,
    metavar = "C",
    nargs = 4,
    type = int,
    help = "Option for rendering with custom color scheme.",
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
        "--background-color",
        default = (255, 255, 255, 255),
        metavar = "C",
        nargs = 4,
        type = int,
        help = "Page background color. It shall be given in RGBA format as a sequence of integers ranging from 0 to 255. Defaults to white.",
    )
    parser.add_argument(
        "--path-fill-color",
        **ColorSchemeOpt
    )
    parser.add_argument(
        "--path-stroke-color",
        **ColorSchemeOpt
    )
    parser.add_argument(
        "--text-fill-color",
        **ColorSchemeOpt
    )
    parser.add_argument(
        "--text-stroke-color",
        **ColorSchemeOpt
    )
    parser.add_argument(
        "--fill-to-stroke",
        action = "store_true",
        help = "Whether fill paths need to be stroked. Ignored if not rendering with custom color scheme.",
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
        help = "Whether to render in greyscale mode (no colors)",
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
    parser.add_argument(
        "--use-numpy",
        action = "store_true",
        help = "Render to numpy arrays as intermediary, then converting to PIL images (for testing only)."
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
        
        color_scheme_kws = dict(
            path_fill_color = args.path_fill_color,
            path_stroke_color = args.path_stroke_color,
            text_fill_color = args.text_fill_color,
            text_stroke_color = args.text_stroke_color,
        )
        color_scheme = None
        if any(color_scheme_kws.values()):
            color_scheme = pdfium.ColorScheme(**color_scheme_kws)
        
        kwargs = dict(
            page_indices = page_indices,
            n_processes = args.processes,
            scale = args.scale,
            rotation = args.rotation,
            crop = args.crop,
            greyscale = args.greyscale,
            color = args.background_color,
            color_scheme = color_scheme,
            fill_to_stroke = args.fill_to_stroke,
            optimise_mode = args.optimise_mode,
            draw_annots = not args.no_annotations,
            draw_forms = not args.no_forms,
            force_halftone = args.force_halftone,
            rev_byteorder = args.rev_byteorder,
            prefer_bgrx = args.prefer_bgrx,
        )
        for type in args.no_antialias:
            kwargs["no_smooth%s" % type] = True
        
        converter = pdfium.BitmapConv.pil_image
        if args.use_numpy:
            converter = pdfium.BitmapConv.numpy_ndarray
        
        prefix = splitext(basename(input_path))[0] + "_"
        n_digits = len(str( max(page_indices)+1 ))
        
        renderer = pdf.render_to(converter, **kwargs)
        
        for result, index in zip(renderer, page_indices):
            if args.use_numpy:
                array, cl_format = result
                if cl_format in UnreverseBitmapStr.keys():
                    raise RuntimeError("PIL.Image.fromarray() can't work with colour format %s. Consider using --rev-byteorder." % cl_format)
                image = PIL.Image.fromarray(array, mode=cl_format)
            else:
                image = result
            suffix = str(index+1).zfill(n_digits)
            output_path = "%s.%s" % (join(args.output, prefix+suffix), args.format)
            image.save(output_path)
            image.close()
        
        pdf.close()
