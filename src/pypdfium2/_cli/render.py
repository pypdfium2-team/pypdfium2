# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import math
import ctypes
import logging
import colorsys
import PIL.Image
import PIL.ImageFilter
import PIL.ImageDraw
import functools
from pathlib import Path
import multiprocessing as mp
import concurrent.futures as ft
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i
import pypdfium2._helpers as pdfium
# CONSIDER dotted access
from pypdfium2._cli._parsers import add_input, get_input, setup_logging

logger = logging.getLogger(__name__)


def _bitmap_wrapper_foreign_simple(width, height, format, *args, **kwargs):
    if format == pdfium_c.FPDFBitmap_BGRx:
        use_alpha = False
    elif format == pdfium_c.FPDFBitmap_BGRA:
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
    # choose some random colors so we can distinguish the different drawings (TODO improve)
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
        "--optimize-mode",
        choices = ("lcd", "print"),
        help = "The rendering optimisation mode. None if not given.",
    )
    parser.add_argument(
        "--crop",
        nargs = 4,
        type = float,
        default = (0, 0, 0, 0),
        help = "Amount to crop from (left, bottom, right, top)",
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
        "--no-antialias",
        nargs = "+",
        default = (),
        choices = ("text", "image", "path"),
        type = str.lower,
        help = "Item types that shall not be smoothed",
    )
    parser.add_argument(
        "--force-halftone",
        action = "store_true",
        help = "Always use halftone for image stretching",
    )
    
    bitmap = parser.add_argument_group(
        title = "Bitmap options",
        description = "Bitmap config, including pixel format. Notes: 1) By default, an alpha channel will be used only if --fill-color has transparency. 2) The combination of --rev-byteorder and --prefer-bgrx may be used to achieve a pixel format natively supported by PIL, to avoid data copying.",
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
        help = "Whether to render in grayscale mode (no colors)",
    )
    # TODO consider making --rev-byteorder and --prefer-bgrx default for PIL
    bitmap.add_argument(
        "--rev-byteorder",
        action = "store_true",
        help = "Render with reverse byte order internally, i. e. RGB(A/X) instead of BGR(A/X). The result should be identical.",
    )
    bitmap.add_argument(
        "--prefer-bgrx",
        action = "store_true",
        help = "Use a four-channel pixel format for colored output, even if rendering without transparency.",
    )
    
    parallel = parser.add_argument_group(
        title = "Parallelization",
        description = "Options for rendering with multiple processes",
    )
    parallel.add_argument(
        "--linear",
        nargs = "?",
        type = int,
        default = 4,
        const = math.inf,
        help = "TODO"
    )
    parallel.add_argument(
        "--processes",
        default = os.cpu_count(),
        type = int,
        help = "The number of parallel rendering processes (defaults to the number of CPU cores)",
    )
    parallel.add_argument(
        "--parallel-strategy",
        choices = ("spawn", "forkserver", "fork"),
        # TODO consider smarter default, e.g. use python default, but if on Linux and using buffer input, then use spawn or forkserver
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
        title = "PDFium forced color scheme",
        description = "Options for rendering with forced color scheme. Note that pdfium is problematic here: It takes color params for certain object types and forces them on all instances in question, regardless of their original color, which means different colors are flattened into one (information loss). This can lead to readability issues. Consider using lightness inversion post-processing instead.",
    )
    color_scheme.add_argument(
        "--sample-theme",
        action = "store_true",
        help = "Use a sample theme as base color scheme. Explicit color params override selectively."
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
    
    postproc = parser.add_argument_group(
        title = "Post processing"
    )
    postproc.add_argument(
        "--invert-lightness",
        action = "store_true",
    )
    postproc.add_argument(
        "--exclude-images",
        action = "store_true",
    )


class SavingReceiver:
    
    def __init__(self, path_parts):
        self._path_parts = path_parts
    
    def get_path(self, i):
        output_dir, prefix, n_digits, format = self._path_parts
        return output_dir / (prefix + "%0*d.%s" % (n_digits, i+1, format))


class PILReceiver (SavingReceiver):
    
    def __call__(self, page, bitmap, index, *args, **kwargs):
        pil_image = pdfium.PdfBitmap.to_pil(bitmap)
        pil_image = self.postprocess(page, pil_image, *args, **kwargs)
        out_path = self.get_path(index)
        pil_image.save(out_path)
        logger.info(f"Wrote page {index+1} as {out_path.name}")
    
    # FIXME code style ...
    
    POSTPROC_LUT_SIZE = 17
    
    @staticmethod
    def _invert_px_lightness(r, g, b):
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        l = 1 - l
        return colorsys.hls_to_rgb(h, l, s)
    
    @staticmethod
    def _convert_point(page, crop, size, rot, point):
        size_x, size_y = size
        page_x, page_y = point
        device_x, device_y = ctypes.c_int(), ctypes.c_int()
        ok = pdfium_c.FPDF_PageToDevice(page, -crop[0], -crop[3], size_x, size_y, rot, page_x, page_y, device_x, device_y)
        assert ok
        return (device_x.value, device_y.value)
    
    def postprocess(self, page, in_image, crop, rot, invert_lightness, exclude_images):
        
        out_image = in_image
        
        if invert_lightness:
            
            pil_filter = PIL.ImageFilter.Color3DLUT.generate(self.POSTPROC_LUT_SIZE, self._invert_px_lightness)
            out_image = in_image.filter(pil_filter)
            
            if exclude_images:
                images = list(page.get_objects([pdfium_c.FPDF_PAGEOBJ_IMAGE]))
                if len(images) > 0:
                    mask = PIL.Image.new("1", in_image.size)
                    draw = PIL.ImageDraw.Draw(mask)
                    for obj in images:
                        quad_bounds = obj.get_quad_bounds()
                        quad_bounds = [self._convert_point(page, crop, in_image.size, pdfium_i.RotationToConst[rot], p) for p in quad_bounds]
                        draw.polygon(quad_bounds, fill=1, outline=1)
                    out_image.paste(in_image, mask=mask)
        
        return out_image


def _render_parallel_init(extra_init, input, password, may_init_forms, kwargs, receiver, receiver_kwargs):
    
    if extra_init:
        extra_init()
    
    logger.info(f"Initializing data for process {os.getpid()}")
    
    pdf = pdfium.PdfDocument(input, password=password, autoclose=True)
    if may_init_forms:
        pdf.init_forms()
    
    global ProcObjs
    ProcObjs = (pdf, kwargs, receiver, receiver_kwargs)


def _render_parallel_job(i):
    logger.info(f"Started page {i+1} ...")
    global ProcObjs
    pdf, kwargs, receiver, receiver_kwargs = ProcObjs
    page = pdf[i]
    bitmap = page.render(**kwargs)
    receiver(page, bitmap, i, **receiver_kwargs)
    page.close()


def main(args):
    
    # TODO turn into a python-usable API yielding output paths as they arrive
    
    pdf = get_input(args)
    
    # TODO move to parsers?
    n_pages = len(pdf)
    if not all(0 <= i < n_pages for i in args.pages):
        raise ValueError("Out-of-bounds page indices are prohibited.")
    if len(args.pages) != len(set(args.pages)):
        raise ValueError("Duplicate page indices are prohibited.")
    
    if not args.prefix:
        args.prefix = f"{args.input.stem}_"
    if not args.fill_color:
        args.fill_color = (0, 0, 0, 255) if args.sample_theme else (255, 255, 255, 255)
    
    cs_kwargs = dict()
    if args.sample_theme:
        cs_kwargs.update(**SampleTheme)
    cs_kwargs.update(**{f: getattr(args, f) for f in CsFields if getattr(args, f)})
    cs = pdfium.PdfColorScheme(**cs_kwargs) if len(cs_kwargs) > 0 else None
    
    may_draw_forms = not args.no_forms
    kwargs = dict(
        scale = args.scale,
        rotation = args.rotation,
        crop = args.crop,
        grayscale = args.grayscale,
        fill_color = args.fill_color,
        color_scheme = cs,
        fill_to_stroke = args.fill_to_stroke,
        optimize_mode = args.optimize_mode,
        draw_annots = not args.no_annotations,
        may_draw_forms = may_draw_forms,
        force_halftone = args.force_halftone,
        rev_byteorder = args.rev_byteorder,
        prefer_bgrx = args.prefer_bgrx,
        bitmap_maker = BitmapMakers[args.bitmap_maker],
    )
    for type in args.no_antialias:
        kwargs[f"no_smooth{type}"] = True
    
    n_digits = len(str(n_pages))
    path_parts = (args.output, args.prefix, n_digits, args.format)
    receiver = PILReceiver(path_parts)
    receiver_kwargs = dict(
        crop = kwargs["crop"],
        rot = kwargs["rotation"],
        invert_lightness = args.invert_lightness,
        exclude_images = args.exclude_images,
    )
    
    if n_pages <= args.linear:
        
        logger.info("Linear rendering ...")
        if may_draw_forms:
            pdf.init_forms()
        
        for i in args.pages:
            logger.info(f"Started page {i+1} ...")
            page = pdf[i]
            bitmap = page.render(**kwargs)
            receiver(page, bitmap, i, **receiver_kwargs)
        
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
        
        extra_init = (setup_logging if args.parallel_strategy in ("spawn", "forkserver") else None)
        pool_kwargs = dict(
            initializer = _render_parallel_init,
            initargs = (extra_init, pdf._orig_input, args.password, may_draw_forms, kwargs, receiver, receiver_kwargs),
        )
        
        with pool_ctor(args.processes, **pool_kwargs) as pool:
            map_func = getattr(pool, map_attr)
            for _ in map_func(_render_parallel_job, args.pages):
                pass
        
        # For shared memory, we must keep the pdf alive up to this point, since it manages input lifetime
        # TODO consider outsourcing input to caller side
        pdf.close()
