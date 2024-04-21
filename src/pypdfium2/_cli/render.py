# SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import math
import logging
import functools
from pathlib import Path
import multiprocessing as mp
import concurrent.futures as ft

try:
    import cv2
except ImportError:
    cv2 = None

import pypdfium2._helpers as pdfium
import pypdfium2.internal as pdfium_i
import pypdfium2.raw as pdfium_r
# TODO? consider dotted access
from pypdfium2._cli._parsers import (
    add_input, get_input,
    setup_logging,
    BooleanOptionalAction,
)

logger = logging.getLogger(__name__)


def _bitmap_wrapper_foreign_simple(width, height, format, *args, **kwargs):
    if format == pdfium_r.FPDFBitmap_BGRx:
        use_alpha = False
    elif format == pdfium_r.FPDFBitmap_BGRA:
        use_alpha = True
    else:
        raise RuntimeError(f"Cannot create foreign_simple bitmap with bitmap type {pdfium_i.BitmapTypeToStr[format]}.")
    return pdfium.PdfBitmap.new_foreign_simple(width, height, use_alpha, *args, **kwargs)

BitmapMakers = dict(
    native = pdfium.PdfBitmap.new_native,
    foreign = pdfium.PdfBitmap.new_foreign,
    foreign_packed = functools.partial(pdfium.PdfBitmap.new_foreign, force_packed=True),
    foreign_simple = _bitmap_wrapper_foreign_simple,
)

CsFields = ("path_fill", "path_stroke", "text_fill", "text_stroke")
ColorOpts = dict(metavar="C", nargs=4, type=int)
SampleTheme = dict(
    # TODO improve colors - currently it's just some random ones to distinguish the different drawings
    path_fill   = (170, 100, 0,   255),  # dark orange
    path_stroke = (0,   150, 255, 255),  # sky blue
    text_fill   = (255, 255, 255, 255),  # white
    text_stroke = (150, 255, 0,   255),  # green
)

def attach(parser):
    add_input(parser, pages=True)
    parser.add_argument(
        "--output", "-o",
        type = Path,
        required = True,
        help = "Output directory where the serially numbered images shall be placed.",
    )
    parser.add_argument(
        "--prefix",
        help = "Custom prefix for the images. Defaults to the input filename's stem.",
    )
    parser.add_argument(
        "--format", "-f",
        default = "jpg",
        type = str.lower,
        help = "The image format to use.",
    )
    parser.add_argument(
        "--engine",
        dest = "engine_cls",
        type = lambda k: {"pil": PILEngine, "numpy+cv2": NumpyCV2Engine}[k.lower()],
        help = "The saver engine to use (pil, numpy+cv2)",
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
        help = "Rotate pages by 90, 180 or 270 degrees.",
    )
    parser.add_argument(
        "--fill-color",
        help = "Color the bitmap will be filled with before rendering. It shall be given in RGBA format as a sequence of integers ranging from 0 to 255. Defaults to white.",
        **ColorOpts,
    )
    parser.add_argument(
        "--optimize-mode",
        choices = ("lcd", "print"),
        help = "The rendering optimisation mode. None if not given.",
    )
    parser.add_argument(
        "--crop",
        nargs = 4,
        type = float,
        default = (0, 0, 0, 0),
        help = "Amount to crop from (left, bottom, right, top).",
    )
    parser.add_argument(
        "--draw-annots",
        action = BooleanOptionalAction,
        default = True,
        help = "Whether annotations may be shown (default: true).",
    )
    parser.add_argument(
        "--draw-forms",
        action = BooleanOptionalAction,
        default = True,
        help = "Whether forms may be shown (default: true).",
    )
    parser.add_argument(
        "--no-antialias",
        nargs = "+",
        default = [],
        choices = ("text", "image", "path"),
        type = str.lower,
        help = "Item types that shall not be smoothed.",
    )
    parser.add_argument(
        "--force-halftone",
        action = "store_true",
        help = "Always use halftone for image stretching.",
    )
    
    bitmap = parser.add_argument_group(
        title = "Bitmap options",
        description = "Bitmap config, including pixel format.",
    )
    bitmap.add_argument(
        "--bitmap-maker",
        choices = BitmapMakers.keys(),
        default = "native",
        help = "The bitmap maker to use.",
        type = str.lower,
    )
    bitmap.add_argument(
        "--grayscale",
        action = "store_true",
        help = "Whether to render in grayscale mode (no colors).",
    )
    bitmap.add_argument(
        "--byteorder",
        dest = "rev_byteorder",
        type = lambda v: {"bgr": False, "rgb": True}[v.lower()],
        help = "Whether to use BGR or RGB byteorder (default: conditional).",
    )
    bitmap.add_argument(
        "--x-channel",
        dest = "prefer_bgrx",
        action = BooleanOptionalAction,
        help = "Whether to prefer BGRx/RGBx over BGR/RGB (default: conditional).",
    )
    
    parallel = parser.add_argument_group(
        title = "Parallelization",
        description = "Options for rendering with multiple processes.",
    )
    parallel.add_argument(
        "--linear",
        nargs = "?",
        type = int,
        const = math.inf,
        help = "Render non-parallel if page count is less or equal to the specified value (default is conditional). If this flag is given without a value, then render linear regardless of document length.",
    )
    parallel.add_argument(
        "--processes",
        default = os.cpu_count(),
        type = int,
        help = "The maximum number of parallel rendering processes. Defaults to the number of CPU cores.",
    )
    parallel.add_argument(
        "--parallel-strategy",
        choices = ("spawn", "forkserver", "fork"),
        default = "spawn",
        type = str.lower,
        help = "The process start method to use. ('fork' is discouraged due to stability issues.)",
    )
    parallel.add_argument(
        "--parallel-lib",
        choices = ("mp", "ft"),
        default = "mp",
        type = str.lower,
        help = "The parallelization module to use (mp = multiprocessing, ft = concurrent.futures).",
    )
    parallel.add_argument(
        "--parallel-map",
        type = str.lower,
        help = "The map function to use (backend specific, the default is an iterative map)."
    )
    
    color_scheme = parser.add_argument_group(
        title = "Forced color scheme",
        description = "Options for using pdfium's forced color scheme renderer. Deprecated, considered not useful.",
    )
    color_scheme.add_argument(
        "--sample-theme",
        action = "store_true",
        help = "Use a dark background sample theme as base. Explicit color params override selectively."
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
        help = "Only draw borders around fill areas using the `path_stroke` color, instead of filling with the `path_fill` color.",
    )


class SavingEngine:
    
    def __init__(self, path_parts):
        self._path_parts = path_parts
    
    def _get_path(self, i):
        output_dir, prefix, n_digits, format = self._path_parts
        return output_dir / f"{prefix}{i+1:0{n_digits}d}.{format}"
    
    def __call__(self, bitmap, i):
        out_path = self._get_path(i)
        self._saving_hook(out_path, bitmap)
        logger.info(f"Wrote page {i+1} as {out_path.name}")


class PILEngine (SavingEngine):
    def _saving_hook(self, out_path, bitmap):
        bitmap.to_pil().save(out_path)

class NumpyCV2Engine (SavingEngine):
    def _saving_hook(self, out_path, bitmap):
        cv2.imwrite(str(out_path), bitmap.to_numpy())


def _render_parallel_init(extra_init, input, password, may_init_forms, kwargs, engine):
    
    if extra_init:
        extra_init()
    
    logger.info(f"Initializing data for process {os.getpid()}")
    
    pdf = pdfium.PdfDocument(input, password=password, autoclose=True)
    if may_init_forms:
        pdf.init_forms()
    
    global ProcObjs
    ProcObjs = (pdf, kwargs, engine)


def _render_job(i, pdf, kwargs, engine):
    # logger.info(f"Started page {i+1} ...")
    page = pdf[i]
    bitmap = page.render(**kwargs)
    engine(bitmap, i)

def _render_parallel_job(i):
    global ProcObjs; _render_job(i, *ProcObjs)


def main(args):
    
    # TODO turn into a python-usable API yielding output paths as they are written
    
    pdf = get_input(args, init_forms=args.draw_forms)
    
    # TODO move to parsers?
    pdf_len = len(pdf)
    if not all(0 <= i < pdf_len for i in args.pages):
        raise ValueError("Out-of-bounds page indices are prohibited.")
    if len(args.pages) != len(set(args.pages)):
        raise ValueError("Duplicate page indices are prohibited.")
    
    if args.prefix is None:
        args.prefix = f"{args.input.stem}_"
    if args.fill_color is None:
        args.fill_color = (0, 0, 0, 255) if args.sample_theme else (255, 255, 255, 255)
    if args.linear is None:
        args.linear = 6 if args.format == "jpg" else 3
    
    # numpy+cv2 is much faster for PNG, and PIL faster for JPG, but this might simply be due to different encoding defaults
    if args.engine_cls is None:
        if cv2 != None and args.format == "png":
            args.engine_cls = NumpyCV2Engine
        else:
            args.engine_cls = PILEngine
    
    # PIL is faster with rev_byteorder and prefer_bgrx = True, as this achieves a natively supported pixel format. For numpy+cv2 there doesn't seem to be a difference.
    if args.rev_byteorder is None:
        args.rev_byteorder = args.engine_cls is PILEngine
    if args.prefer_bgrx is None:
        # PIL can't save BGRX as PNG
        args.prefer_bgrx = args.engine_cls is PILEngine and args.format != "png"
    
    cs_kwargs = dict()
    if args.sample_theme:
        cs_kwargs.update(**SampleTheme)
    cs_kwargs.update(**{f: getattr(args, f) for f in CsFields if getattr(args, f)})
    cs = pdfium.PdfColorScheme(**cs_kwargs) if len(cs_kwargs) > 0 else None
    
    kwargs = dict(
        scale = args.scale,
        rotation = args.rotation,
        crop = args.crop,
        grayscale = args.grayscale,
        fill_color = args.fill_color,
        color_scheme = cs,
        fill_to_stroke = args.fill_to_stroke,
        optimize_mode = args.optimize_mode,
        draw_annots = args.draw_annots,
        may_draw_forms = args.draw_forms,
        force_halftone = args.force_halftone,
        rev_byteorder = args.rev_byteorder,
        prefer_bgrx = args.prefer_bgrx,
        bitmap_maker = BitmapMakers[args.bitmap_maker],
    )
    for type in args.no_antialias:
        kwargs[f"no_smooth{type}"] = True
    
    # TODO dump all args except password?
    logger.info(f"{args.engine_cls.__name__}, Format: {args.format}, rev_byteorder: {args.rev_byteorder}, prefer_bgrx {args.prefer_bgrx}")
    
    n_digits = len(str(pdf_len))
    path_parts = (args.output, args.prefix, n_digits, args.format)
    engine = args.engine_cls(path_parts)
    
    if len(args.pages) <= args.linear:
        
        logger.info("Linear rendering ...")
        for i in args.pages:
            _render_job(i, pdf, kwargs, engine)
        
    else:
        
        logger.info("Parallel rendering ...")
        
        ctx = mp.get_context(args.parallel_strategy)
        # TODO unify using mp.pool.Pool(context=...) ?
        pool_backends = dict(
            mp = (ctx.Pool, "imap"),
            ft = (functools.partial(ft.ProcessPoolExecutor, mp_context=ctx), "map"),
        )
        pool_ctor, map_attr = pool_backends[args.parallel_lib]
        if args.parallel_map:
            map_attr = args.parallel_map
        
        extra_init = (setup_logging if args.parallel_strategy in ("spawn", "forkserver") else None)
        pool_kwargs = dict(
            initializer = _render_parallel_init,
            initargs = (extra_init, pdf._input, args.password, args.draw_forms, kwargs, engine),
        )
        
        n_procs = min(args.processes, len(args.pages))
        with pool_ctor(n_procs, **pool_kwargs) as pool:
            map_func = getattr(pool, map_attr)
            for _ in map_func(_render_parallel_job, args.pages):
                pass
