# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import logging
from pathlib import Path
import pypdfium2._helpers as pdfium
# TODO? consider dotted access
from pypdfium2._cli._parsers import add_input, get_input

logger = logging.getLogger(__name__)


ColorOpts = dict(
    metavar = "C",
    nargs = 4,
    type = int,
)


def attach(parser):
    add_input(parser, pages=True)
    parser.add_argument(
        "--output", "-o",
        type = Path,
        required = True,
        help = "Output directory where to place the serially numbered images",
    )
    parser.add_argument(
        "--format", "-f",
        default = "jpg",
        help = "The image format to use",
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
        "--fill-color",
        default = (255, 255, 255, 255),
        help = "Color the bitmap will be filled with before rendering. It shall be given in RGBA format as a sequence of integers ranging from 0 to 255. Defaults to white.",
        **ColorOpts,
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
        "--optimize-mode",
        choices = ("lcd", "print"),
        help = "Select a rendering optimisation mode (lcd, print)",
    )
    parser.add_argument(
        "--grayscale",
        action = "store_true",
        help = "Whether to render in grayscale mode (no colors)",
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
        help = "Request the use of a four-channel pixel format for colored output, even if rendering without transparency.",
    )
    parser.add_argument(
        "--processes",
        default = os.cpu_count(),
        type = int,
        help = "The number of processes to use for rendering (defaults to the number of CPU cores)",
    )
    
    color_scheme = parser.add_argument_group(
        title = "Color scheme",
        description = "Options for rendering with custom color scheme",
    )
    color_scheme.add_argument(
        "--path-fill",
        **ColorOpts
    )
    color_scheme.add_argument(
        "--path-stroke",
        **ColorOpts
    )
    color_scheme.add_argument(
        "--text-fill",
        **ColorOpts
    )
    color_scheme.add_argument(
        "--text-stroke",
        **ColorOpts
    )
    color_scheme.add_argument(
        "--fill-to-stroke",
        action = "store_true",
        help = "Whether fill paths need to be stroked.",
    )


class PILSaver:
    
    def __init__(self, fn_args):
        self._fn_args = fn_args
    
    def __call__(self, bitmap, index):
        out_dir, out_prefix, out_suffix, n_digits, format = self._fn_args
        out_path = out_dir / (out_prefix + out_suffix % (n_digits, index+1, format))
        pil_image = pdfium.PdfBitmap.to_pil(bitmap)
        pil_image.save(out_path)
        # return out_path


def main(args):
    
    pdf = get_input(args)
    pdf.init_forms()
    
    cs_kwargs = dict(
        path_fill = args.path_fill,
        path_stroke = args.path_stroke,
        text_fill = args.text_fill,
        text_stroke = args.text_stroke,
    )
    cs = None
    if all(cs_kwargs.values()):
        cs = pdfium.PdfColorScheme(
            fill_to_stroke = args.fill_to_stroke,
            **cs_kwargs,
        )
    elif any(cs_kwargs.values()):
        raise ValueError("If rendering with custom color scheme, all parameters need to be set explicitly.")
    
    kwargs = dict(
        page_indices = args.pages,
        n_processes = args.processes,
        scale = args.scale,
        rotation = args.rotation,
        crop = args.crop,
        grayscale = args.grayscale,
        fill_color = args.fill_color,
        color_scheme = cs,
        optimize_mode = args.optimize_mode,
        draw_annots = not args.no_annotations,
        may_draw_forms = not args.no_forms,
        force_halftone = args.force_halftone,
        rev_byteorder = args.rev_byteorder,
        prefer_bgrx = args.prefer_bgrx,
    )
    for type in args.no_antialias:
        kwargs[f"no_smooth{type}"] = True
    
    n_digits = len(str( max(args.pages)+1 ))
    converter = PILSaver( (args.output, args.input.stem, "_%0*d.%s", n_digits, args.format) )
    
    for _ in pdf.render(converter, **kwargs): pass
