# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import logging
from pathlib import Path
import pypdfium2._helpers as pdfium
# CONSIDER dotted access
from pypdfium2._cli._parsers import add_input, get_input, setup_logging

logger = logging.getLogger(__name__)


CsFields = ("path_fill", "path_stroke", "text_fill", "text_stroke")
ColorOpts = dict(metavar="C", nargs=4, type=int)
DefaultDarkTheme = dict(
    path_fill   = (255, 255, 255, 255),
    path_stroke = (255, 255, 255, 255),
    text_fill   = (255, 255, 255, 255),
    text_stroke = (255, 255, 255, 255),
)


def attach(parser):
    add_input(parser, pages=True)
    parser.add_argument(
        "--output", "-o",
        type = Path,
        required = True,
        help = "Output directory where the serially numbered images shall be placed",
    )
    parser.add_argument(
        "--prefix",
        help = "Custom prefix for the images. Defaults to the input filename's stem.",
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
        help = "The rendering optimisation mode. None if not given.",
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
    
    parallel = parser.add_argument_group(
        title = "Parallelization",
        description = "Options for rendering with multiple processes",
    )
    parallel.add_argument(
        "--linear",
        action = "store_true",
        help = "Render linear in the main process without parallelization. Options of this group will be silently ignored.",
    )
    parallel.add_argument(
        "--processes",
        default = os.cpu_count(),
        type = int,
        help = "The number of parallel rendering processes (defaults to the number of CPU cores)",
    )
    parallel.add_argument(
        "--mp-strategy",
        choices = ("spawn", "forkserver", "fork"),
        default = "spawn",
        help = "The process start method to use. ('fork' is discouraged due to stability issues.)",
    )
    parallel.add_argument(
        "--mp-backend",
        choices = ("mp", "ft"),
        default = "mp",
        help = "The backend to use (mp = multiprocessing, ft = concurrent.futures).",
    )
    
    color_scheme = parser.add_argument_group(
        title = "Color scheme",
        description = "Options for rendering with custom color scheme",
    )
    color_scheme.add_argument(
        "--dark-theme",
        action = "store_true",
        help = "Use a dark theme as base color scheme. Explicit config overrides selectively."
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


class SavingPILConverter:
    
    def __init__(self, output_dir, prefix, n_digits, format):
        self.output_dir, self.prefix, self.n_digits, self.format = output_dir, prefix, n_digits, format
    
    def __call__(self, bitmap, index, **kwargs):
        pil_image = pdfium.PdfBitmap.to_pil(bitmap)
        out = self.output_dir / (self.prefix + "%0*d.%s" % (self.n_digits, index+1, self.format))
        pil_image.save(out)
        # return out


def render_linear(pdf, page_indices, converter, **kwargs):
    for i in page_indices:
        logger.info(f"Rendering page {i+1} ...")
        bitmap = pdf[i].render(**kwargs)
        yield converter(bitmap, index=i)


def main(args):
    
    pdf = get_input(args)
    pdf.init_forms()
    
    if not args.prefix:
        args.prefix = f"{args.input.stem}_"
    if not args.fill_color:
        args.fill_color = (0, 0, 0, 255) if args.dark_theme else (255, 255, 255, 255)
    
    cs_kwargs = dict()
    if args.dark_theme:
        cs_kwargs.update(**DefaultDarkTheme)
    cs_kwargs.update(**{f: getattr(args, f) for f in CsFields if getattr(args, f)})
    cs = pdfium.PdfColorScheme(**cs_kwargs) if len(cs_kwargs) > 0 else None
    
    kwargs = dict(
        page_indices = args.pages,
        scale = args.scale,
        rotation = args.rotation,
        crop = args.crop,
        grayscale = args.grayscale,
        fill_color = args.fill_color,
        color_scheme = cs,
        fill_to_stroke = args.fill_to_stroke,
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
    converter = SavingPILConverter(args.output, args.prefix, n_digits, args.format)
    
    if args.linear:
        logger.info("Linear rendering ...")
        renderer = render_linear(pdf, converter=converter, **kwargs)
    else:
        logger.info("Parallel rendering ...")
        kwargs.update(
            n_processes = args.processes,
            mp_strategy = args.mp_strategy,
            mp_backend = args.mp_backend,
            pool_kwargs = dict(),
        )
        if args.mp_strategy in ("spawn", "forkserver"):
            # it looks like setup_logging() is not run automatically with these mp strategies, so set it as initializer
            kwargs["pool_kwargs"]["initializer"] = setup_logging
        renderer = pdf.render(converter, **kwargs)
    
    for _ in renderer: pass  # produce without storing anything
