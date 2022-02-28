# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import math
import ctypes
from PIL import Image
from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers.constants import OptimiseMode
from pypdfium2._helpers.utilities import (
    colour_as_hex,
    translate_rotation,
)


def _get_pixel_fmt(use_alpha, greyscale):
    
    pixel_fmt = "RGBA", "BGRA", pdfium.FPDFBitmap_BGRA
    
    if not use_alpha:
        if greyscale:
            pixel_fmt = "L", "L", pdfium.FPDFBitmap_Gray
        else:
            pixel_fmt = "RGB", "BGR", pdfium.FPDFBitmap_BGR
    
    return pixel_fmt


def render_page(
        pdf,
        page_index = 0,
        scale = 1,
        rotation = 0,
        colour = (255, 255, 255, 255),
        annotations = True,
        greyscale = False,
        optimise_mode = OptimiseMode.none,
    ):
    """
    Rasterise a single PDF page using PDFium.
    
    Parameters:
        
        pdf (``FPDF_DOCUMENT``):
            A raw PDFium document handle.
        
        page_index (int):
            Zero-based index of the page to render.
        
        scale (float):
            
            Define the quality (or size) of the image.
            
            By default, one PDF point (1/72in) is rendered to 1x1 pixel. This factor scales the
            number of pixels that represent one point.
            
            Higher values increase quality, file size and rendering duration, while lower values
            reduce them.
            
            Note that UserUnit is not taken into account, so if you are using PyPDFium2 in
            conjunction with an other PDF library, you may want to check for a possible
            ``/UserUnit`` in the page dictionary and multiply this scale factor with it.
        
        rotation (int):
            Rotate the page by 90, 180, or 270 degrees. Value 0 means no rotation.
        
        colour (None | typing.Tuple[int, int, int, typing.Optional[int]]):
            Page background colour. Defaults to white.
            It can either be :data:`None`, or values of red, green, blue, and alpha ranging from 0 to 255.
            If :data:`None`, the bitmap will not be filled with a colour, resulting in transparent
            background.
            For RGB, 0 will include nothing of the colour in question, while 255 will completely
            include it. For Alpha, 0 means full transparency, while 255 means no transparency.
        
        annotations (bool):
            Whether to render page annotations.
        
        greyscale (bool):
            Whether to render in greyscale mode (no colours).
        
        optimise_mode (OptimiseMode):
            Optimise rendering for LCD displays or for printing.
    
    Returns:
        :class:`PIL.Image.Image`
    """
    
    if colour is None:
        fpdf_colour, use_alpha = None, True
    else:
        fpdf_colour, use_alpha = colour_as_hex(*colour)
    
    px_target, px_source, px_pdfium = _get_pixel_fmt(use_alpha, greyscale)
    n_px_values = len(px_source)
    
    page_count = pdfium.FPDF_GetPageCount(pdf)
    if not 0 <= page_index < page_count:
        raise IndexError(
            "Page index {} is out of bounds for document with {} pages.".format(page_index, page_count)
        )
    
    form_config = pdfium.FPDF_FORMFILLINFO(2)
    form_fill = pdfium.FPDFDOC_InitFormFillEnvironment(pdf, form_config)
    
    page = pdfium.FPDF_LoadPage(pdf, page_index)
    pdfium.FORM_OnAfterLoadPage(page, form_fill)
    
    width  = math.ceil(pdfium.FPDF_GetPageWidthF(page)  * scale)
    height = math.ceil(pdfium.FPDF_GetPageHeightF(page) * scale)
    
    if rotation in (90, 270):
        width, height = height, width
    
    bitmap = pdfium.FPDFBitmap_CreateEx(
        width,
        height,
        px_pdfium,
        None,
        width * n_px_values,
    )
    if fpdf_colour is not None:
        pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, fpdf_colour)
    
    render_flags = 0x00
    
    if annotations:
        render_flags |= pdfium.FPDF_ANNOT
    if greyscale:
        render_flags |= pdfium.FPDF_GRAYSCALE
    
    if optimise_mode is OptimiseMode.none:
        pass
    elif optimise_mode is OptimiseMode.lcd_display:
        render_flags |= pdfium.FPDF_LCD_TEXT
    elif optimise_mode is OptimiseMode.printing:
        render_flags |= pdfium.FPDF_PRINTING
    else:
        raise ValueError("Invalid optimise_mode {}".format(optimise_mode))
    
    render_args = [
        bitmap,
        page,
        0, 0,
        width, height,
        translate_rotation(rotation),
        render_flags,
    ]
    
    pdfium.FPDF_RenderPageBitmap(*render_args)
    pdfium.FPDF_FFLDraw(form_fill, *render_args)
    
    cbuffer = pdfium.FPDFBitmap_GetBuffer(bitmap)
    buffer = ctypes.cast(cbuffer, ctypes.POINTER(ctypes.c_ubyte * (width * height * n_px_values)))
    
    pil_image = Image.frombuffer(px_target, (width, height), buffer.contents, "raw", px_source, 0, 1)
    
    pdfium.FPDFBitmap_Destroy(bitmap)
    pdfium.FORM_OnBeforeClosePage(page, form_fill)
    pdfium.FPDF_ClosePage(page)
    pdfium.FPDFDOC_ExitFormFillEnvironment(form_fill)
    
    return pil_image
