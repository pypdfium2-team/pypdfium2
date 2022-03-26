# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import math
import ctypes
from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers.constants import OptimiseMode
from pypdfium2._helpers.utilities import (
    colour_as_hex,
    translate_rotation,
)

try:
    from PIL import Image
except ImportError:
    have_pil = False
else:
    have_pil = True


def _get_clformat(use_alpha, greyscale):
    
    px = 'BGRA', pdfium.FPDFBitmap_BGRA
    
    if not use_alpha:
        if greyscale:
            px = 'L', pdfium.FPDFBitmap_Gray
        else:
            px = 'BGR', pdfium.FPDFBitmap_BGR
    
    return px


_clformat_pil = {
    'BGRA': 'RGBA',
    'BGR': 'RGB',
    'L': 'L',
}


class BitmapDataHolder:
    """
    Class to store a bitmap handle and the pointer to its data.
    
    Parameters:
        bm_handle (``FPDF_BITMAP``): Handle to a PDFium bitmap.
        bm_array_ptr (``LP_c_ubyte_Array_[N]``): Pointer to ctypes bitmap data.
    """
    
    def __init__(self, bm_handle, bm_array_ptr):
        self.bm_handle = bm_handle
        self.bm_array_ptr = bm_array_ptr
    
    def get_data(self):
        """ Retrieve the raw ctypes data from ``bm_array_ptr.contents`` (``c_ubyte_Array_[N]``). """
        return self.bm_array_ptr.contents
    
    def close(self):
        """ Release resources associated to the bitmap. """
        pdfium.FPDFBitmap_Destroy(self.bm_handle)


def render_page_base(
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
    Render a single PDF page to ctypes data using PDFium.
    Base function for :func:`.render_pdf_tobytes` and :func:`.render_pdf_topil`.
    
    Parameters:
        
        pdf (``FPDF_DOCUMENT``):
            A raw PDFium document handle.
        
        page_index (int):
            Zero-based index of the page to render.
        
        scale (float):
            Define the quality (or size) of the image.
            By default, one PDF point (1/72in) is rendered to 1x1 pixel. This factor scales the number of pixels that represent one point.
            Higher values increase quality, file size and rendering duration, while lower values reduce them.
            Note that UserUnit is not taken into account, so if you are using pypdfium2 in conjunction with an other PDF library, you may want to check for a possible ``/UserUnit`` in the page dictionary and multiply this scale factor with it.
        
        rotation (int):
            Rotate the page by 90, 180, or 270 degrees. Value 0 means no rotation.
        
        colour (None | typing.Tuple[int, int, int, typing.Optional[int]]):
            Page background colour. Defaults to white.
            It can either be :data:`None`, or values of red, green, blue, and alpha ranging from 0 to 255.
            If :data:`None`, the bitmap will not be filled with a colour, resulting in transparent background.
            For RGB, 0 will include nothing of the colour in question, while 255 will completely include it. For Alpha, 0 means full transparency, while 255 means no transparency.
        
        annotations (bool):
            Whether to render page annotations.
        
        greyscale (bool):
            Whether to render in greyscale mode (no colours).
        
        optimise_mode (OptimiseMode):
            Optimise rendering for LCD displays or for printing.
    
    Returns:
    
        :class:`BitmapDataHolder`, :class:`str`, ``Tuple[int, int]`` – Bitmap data holder, used colour format, and image size.
        
        Call :meth:`BitmapDataHolder.get_data` to obtain the raw ctypes byte array. ``bytes(data_holder.get_data())`` may be used to acquire an independent copy of the data as Python bytes. When you have finished working with the ctypes byte array, call :meth:`BitmapDataHolder.close` to release allocated memory.
        
        The colour format can be ``BGRA``, ``BGR``, or ``L``, depending on the parameters *colour* and *greyscale*.
        
        The image size is given in pixels as a tuple (width, height).
    """
    
    if colour is None:
        fpdf_colour, use_alpha = None, True
    else:
        fpdf_colour, use_alpha = colour_as_hex(*colour)
    
    cl_format, cl_pdfium = _get_clformat(use_alpha, greyscale)
    n_colours = len(cl_format)
    
    page_count = pdfium.FPDF_GetPageCount(pdf)
    if not 0 <= page_index < page_count:
        raise IndexError( "Page index {} is out of bounds for document with {} pages.".format(page_index, page_count) )
    
    form_config = pdfium.FPDF_FORMFILLINFO(2)
    form_fill = pdfium.FPDFDOC_InitFormFillEnvironment(pdf, form_config)
    page = pdfium.FPDF_LoadPage(pdf, page_index)
    
    width = math.ceil(pdfium.FPDF_GetPageWidthF(page) * scale)
    height = math.ceil(pdfium.FPDF_GetPageHeightF(page) * scale)
    if rotation in (90, 270):
        width, height = height, width
    
    bitmap = pdfium.FPDFBitmap_CreateEx(width, height, cl_pdfium, None, width*n_colours)
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
        raise ValueError( "Invalid optimise_mode {}".format(optimise_mode) )
    
    render_args = (bitmap, page, 0, 0, width, height, translate_rotation(rotation), render_flags)
    pdfium.FPDF_RenderPageBitmap(*render_args)
    pdfium.FPDF_FFLDraw(form_fill, *render_args)
    
    cbuf_ptr = pdfium.FPDFBitmap_GetBuffer(bitmap)
    cbuf_array_ptr = ctypes.cast(cbuf_ptr, ctypes.POINTER(ctypes.c_ubyte * (width*height*n_colours)))
    data_holder = BitmapDataHolder(bitmap, cbuf_array_ptr)
    
    pdfium.FPDF_ClosePage(page)
    pdfium.FPDFDOC_ExitFormFillEnvironment(form_fill)
    
    return data_holder, cl_format, (width, height)


def render_page_tobytes(*args, **kws):
    """
    Render a single page to bytes. Parameters are the same as for :func:`.render_page_base`.
    
    Returns:
         :class:`bytes`, :class:`str`, Tuple[int, int]
    """
    data_holder, cl_format, size = render_page_base(*args, **kws)
    data = bytes( data_holder.get_data() )
    data_holder.close()
    return data, cl_format, size


def render_page_topil(*args, **kws):
    """
    Render a single page to a :mod:`PIL` image. Parameters are the same as for :func:`.render_page_base`.
    
    Returns:
        :class:`PIL.Image.Image`
    """
    
    if not have_pil:
        raise RuntimeError("Pillow library needs to be installed for render_page_topil().")
    
    data_holder, cl_format, size = render_page_base(*args, **kws)
    pil_image = Image.frombytes(_clformat_pil[cl_format], size, data_holder.get_data(), "raw", cl_format, 0, 1)
    data_holder.close()
    
    return pil_image
