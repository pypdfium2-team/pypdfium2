# SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import math
import logging
import colorsys
import functools
from pathlib import Path
import multiprocessing as mp
import concurrent.futures as ft
from importlib.util import find_spec

import pypdfium2._helpers as pdfium
import pypdfium2.internal as pdfium_i
import pypdfium2.raw as pdfium_r
from pypdfium2._cli._parsers import (
    add_input, get_input,
    setup_logging,
    BooleanOptionalAction,
)

have_pil = find_spec("PIL") is not None
have_cv2 = find_spec("cv2") is not None
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
        metavar="C", nargs=4, type=int,
        help = "Color the bitmap will be filled with before rendering. Shall be given in RGBA format as a sequence of integers ranging from 0 to 255. Defaults to white.",
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
    
    postproc = parser.add_argument_group(
        title = "Post processing",
        description = "Options to post-process rendered images. Note, this may have a strongly negative impact on performance.",
    )
    postproc.add_argument(
        "--invert-lightness",
        action = "store_true",
        help = "Invert lightness using the HLS color space (e.g. white<->black, dark_blue<->light_blue). The intent is to achieve a dark theme for documents with light background, while providing better visual results than classical color inversion or a flat pdfium color scheme.",
    )
    postproc.add_argument(
        "--exclude-images",
        action = "store_true",
        help = "Whether to exclude PDF images from lightness inversion.",
    )


class SavingEngine:
    
    def __init__(self, path_parts, postproc_kwargs):
        self._path_parts = path_parts
        self.postproc_kwargs = postproc_kwargs
    
    def _get_path(self, i):
        output_dir, prefix, n_digits, format = self._path_parts
        return output_dir / f"{prefix}{i+1:0{n_digits}d}.{format}"
    
    def __call__(self, i, bitmap, page):
        out_path = self._get_path(i)
        self._saving_hook(out_path, bitmap, page, self.postproc_kwargs)
        logger.info(f"Wrote page {i+1} as {out_path.name}")


class PILEngine (SavingEngine):
    
    def do_imports(self):
        if not self.postproc_kwargs["invert_lightness"]:
            return
        global PIL
        import PIL.Image
        import PIL.ImageOps
        import PIL.ImageFilter
        import PIL.ImageDraw
    
    def _saving_hook(self, out_path, bitmap, page, postproc_kwargs):
        posconv = bitmap.get_posconv(page)
        pil_image = bitmap.to_pil()
        pil_image = self.postprocess(pil_image, page, posconv, **postproc_kwargs)
        pil_image.save(out_path)
    
    @staticmethod
    def _invert_px_lightness(r, g, b):
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        l = 1 - l
        return colorsys.hls_to_rgb(h, l, s)
    
    LINV_LUT_SIZE = 17
    
    @classmethod
    @functools.lru_cache(maxsize=1)
    def _get_linv_lut(cls):
        return PIL.ImageFilter.Color3DLUT.generate(cls.LINV_LUT_SIZE, cls._invert_px_lightness)
    
    @classmethod
    def postprocess(cls, src_image, page, posconv, invert_lightness, exclude_images):
        dst_image = src_image
        if invert_lightness:
            if src_image.mode == "L":
                dst_image = PIL.ImageOps.invert(src_image)
            else:
                dst_image = dst_image.filter(cls._get_linv_lut())
            if exclude_images:
                # don't descend into XObjects as I'm not sure how to translate XObject to page coordinates
                image_objs = list(page.get_objects([pdfium_r.FPDF_PAGEOBJ_IMAGE], max_depth=1))
                if len(image_objs) > 0:
                    mask = PIL.Image.new("1", src_image.size)
                    draw = PIL.ImageDraw.Draw(mask)
                    for obj in image_objs:
                        qpoints = [posconv.to_bitmap(x, y) for x, y in obj.get_quad_points()]
                        draw.polygon(qpoints, fill=1)
                    dst_image.paste(src_image, mask=mask)
        return dst_image


class NumpyCV2Engine (SavingEngine):
    
    def do_imports(self):
        global cv2, np
        import cv2
        if self.postproc_kwargs["exclude_images"]:
            import numpy as np
    
    def _saving_hook(self, out_path, bitmap, page, postproc_kwargs):
        np_array = bitmap.to_numpy()
        np_array = self.postprocess(np_array, bitmap, page, **postproc_kwargs)
        cv2.imwrite(str(out_path), np_array)
    
    @classmethod
    def postprocess(cls, src_image, bitmap, page, invert_lightness, exclude_images):
        dst_image = src_image
        
        if invert_lightness:
            
            if bitmap.format == pdfium_r.FPDFBitmap_Gray:
                dst_image = 255 - src_image
            else:
                
                if bitmap.rev_byteorder:
                    convert_to = cv2.COLOR_RGB2HLS
                    convert_from = cv2.COLOR_HLS2RGB
                else:
                    convert_to = cv2.COLOR_BGR2HLS
                    convert_from = cv2.COLOR_HLS2BGR
                
                dst_image = cv2.cvtColor(dst_image, convert_to)
                h, l, s = cv2.split(dst_image)
                l = ~l
                dst_image = cv2.merge([h, l, s])
                dst_image = cv2.cvtColor(dst_image, convert_from)
            
            if exclude_images:
                assert bitmap.format != pdfium_r.FPDFBitmap_BGRx, "Not sure how to paste with mask on {RGB,BGR}X image using cv2"
                posconv = bitmap.get_posconv(page)
                image_objs = list(page.get_objects([pdfium_r.FPDF_PAGEOBJ_IMAGE], max_depth=1))
                if len(image_objs) > 0:
                    mask = np.zeros((bitmap.height, bitmap.width, 1), np.uint8)
                    for obj in image_objs:
                        qpoints = np.array([posconv.to_bitmap(x, y) for x, y in obj.get_quad_points()], np.int32)
                        cv2.fillPoly(mask, [qpoints], 1)
                    dst_image = cv2.copyTo(src_image, mask=mask, dst=dst_image)
            
        return dst_image


def _render_parallel_init(logging_init, engine_init, input, password, may_init_forms, kwargs, engine):
    
    logging_init()
    logger.info(f"Initializing data for process {os.getpid()}")
    engine_init()
    
    pdf = pdfium.PdfDocument(input, password=password, autoclose=True)
    if may_init_forms:
        pdf.init_forms()
    
    global ProcObjs
    ProcObjs = (pdf, kwargs, engine)


def _render_job(i, pdf, kwargs, engine):
    # logger.info(f"Started page {i+1} ...")
    page = pdf[i]
    bitmap = page.render(**kwargs)
    engine(i, bitmap, page)

def _render_parallel_job(i):
    global ProcObjs
    _render_job(i, *ProcObjs)

def _do_nothing(): pass


# TODO turn into a python-usable API yielding output paths as they are written
def main(args):
    
    pdf = get_input(args, init_forms=args.draw_forms)
    
    pdf_len = len(pdf)
    if not all(0 <= i < pdf_len for i in args.pages):
        raise ValueError("Out-of-bounds page indices are prohibited.")
    if len(args.pages) != len(set(args.pages)):
        raise ValueError("Duplicate page indices are prohibited.")
    
    if args.prefix is None:
        args.prefix = f"{args.input.stem}_"
    if args.fill_color is None:
        args.fill_color = (255, 255, 255, 255)
    if args.linear is None:
        args.linear = 6 if args.format == "jpg" else 3
    
    # numpy+cv2 is much faster for PNG, and PIL faster for JPG, but this might simply be due to different encoding defaults
    if args.engine_cls is None:
        assert have_pil or have_cv2, "Either pillow or numpy+cv2 must be installed for rendering CLI."
        if (not have_pil) or (have_cv2 and args.format == "png"):
            args.engine_cls = NumpyCV2Engine
        else:
            args.engine_cls = PILEngine
    
    # PIL is faster with rev_byteorder and prefer_bgrx = True, as this achieves a natively supported pixel format. For numpy+cv2 there doesn't seem to be a difference.
    if args.rev_byteorder is None:
        args.rev_byteorder = args.engine_cls is PILEngine
    if args.prefer_bgrx is None:
        # PIL can't save BGRX as PNG
        args.prefer_bgrx = args.engine_cls is PILEngine and args.format != "png"
    
    kwargs = dict(
        scale = args.scale,
        rotation = args.rotation,
        crop = args.crop,
        grayscale = args.grayscale,
        fill_color = args.fill_color,
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
    
    postproc_kwargs = dict(
        invert_lightness = args.invert_lightness,
        exclude_images = args.exclude_images,
    )
    
    # TODO dump all args except password?
    logger.info(f"{args.engine_cls.__name__}, Format: {args.format}, rev_byteorder: {args.rev_byteorder}, prefer_bgrx {args.prefer_bgrx}")
    
    n_digits = len(str(pdf_len))
    path_parts = (args.output, args.prefix, n_digits, args.format)
    engine = args.engine_cls(path_parts, postproc_kwargs)
    
    if len(args.pages) <= args.linear:
        
        logger.info("Linear rendering ...")
        engine.do_imports()
        for i in args.pages:
            _render_job(i, pdf, kwargs, engine)
        
    else:
        
        logger.info("Parallel rendering ...")
        
        ctx = mp.get_context(args.parallel_strategy)
        pool_backends = dict(
            mp = (ctx.Pool, "imap"),
            ft = (functools.partial(ft.ProcessPoolExecutor, mp_context=ctx), "map"),
        )
        pool_ctor, map_attr = pool_backends[args.parallel_lib]
        if args.parallel_map:
            map_attr = args.parallel_map
        
        if args.parallel_strategy == "fork":
            logging_init, engine_init = _do_nothing, _do_nothing
            engine.do_imports()
        else:
            logging_init, engine_init = setup_logging, engine.do_imports
        
        pool_kwargs = dict(
            initializer = _render_parallel_init,
            initargs = (logging_init, engine_init, pdf._input, args.password, args.draw_forms, kwargs, engine),
        )
        
        n_procs = min(args.processes, len(args.pages))
        with pool_ctor(n_procs, **pool_kwargs) as pool:
            map_func = getattr(pool, map_attr)
            for _ in map_func(_render_parallel_job, args.pages):
                pass
