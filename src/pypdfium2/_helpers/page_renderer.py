# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import math
import ctypes
from PIL import Image
from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers import utilities
from pypdfium2._helpers.constants import *


def render_page(
        pdf: pdfium.FPDF_DOCUMENT,
        page_index: int = 0,
        scale: float = 1,
        rotation: int = 0,
        colour: int = 0xFFFFFFFF,
        annotations: bool = True,
        greyscale: bool = False,
        optimise_mode: OptimiseMode = OptimiseMode.none,
    ) -> Image.Image:
    """
    Rasterise a single PDF page using PDFium.
    
    Parameters:
        
        pdf:
            A PDFium document (can be obtained with :class:`.PdfContext` or :func:`.open_pdf_auto`).
        
        page_index:
            Zero-based index of the page to render.
        
        scale:
            
            Define the quality (or size) of the image.
            
            By default, one PDF point (1/72in) is rendered to 1x1 pixel. This factor scales the
            number of pixels that represent one point.
            
            Higher values increase quality, file size and rendering duration, while lower values
            reduce them.
            
            Note that UserUnit is not taken into account, so if you are using PyPDFium2 in
            conjunction with an other PDF library, you may want to check for a possible
            ``/UserUnit`` in the page dictionary and multiply this scale factor with it.
        
        rotation:
            Rotate the page by 90, 180, or 270 degrees. Value 0 means no rotation.
        
        colour:
            
            .. _8888 ARGB: https://en.wikipedia.org/wiki/RGBA_color_model#ARGB32
            
            The background colour to use, given as a hexadecimal integer in `8888 ARGB`_ format.
            Defaults to white (``0xFFFFFFFF``). See also :func:`.colour_as_hex`.
        
        annotations:
            Whether to render page annotations.
        
        greyscale:
            Whether to render in greyscale mode (no colours).
        
        optimise_mode:
            Optimise rendering for LCD displays or for printing.
    
    Returns:
        :class:`PIL.Image.Image`
    """
    
    use_alpha = True
    
    if colour is not None:
        alpha_val = hex(colour)[2:4].upper()
        if alpha_val == 'FF':
            use_alpha = False
    
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
    
    bitmap = pdfium.FPDFBitmap_Create(width, height, int(use_alpha))
    if colour is not None:
        pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, colour)
    
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
        utilities.translate_rotation(rotation),
        render_flags,
    ]
    
    pdfium.FPDF_RenderPageBitmap(*render_args)
    pdfium.FPDF_FFLDraw(form_fill, *render_args)
    
    cbuffer = pdfium.FPDFBitmap_GetBuffer(bitmap)
    buffer = ctypes.cast(cbuffer, ctypes.POINTER(ctypes.c_ubyte * (width * height * 4)))
    
    pil_image = Image.frombuffer("RGBA", (width, height), buffer.contents, "raw", "BGRA", 0, 1)
    
    if greyscale:
        if use_alpha:
            pil_image = pil_image.convert("LA")
        else:
            pil_image = pil_image.convert("L")
    
    elif not use_alpha:
        pil_image = pil_image.convert("RGB")
    
    pdfium.FPDFBitmap_Destroy(bitmap)
    pdfium.FORM_OnBeforeClosePage(page, form_fill)
    pdfium.FPDF_ClosePage(page)
    pdfium.FPDFDOC_ExitFormFillEnvironment(form_fill)
    
    return pil_image
