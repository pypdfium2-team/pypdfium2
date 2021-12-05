# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import math
import ctypes
import logging
import tempfile
from PIL import Image
import concurrent.futures
from os.path import abspath
from typing import Optional

from pypdfium2._constants import *
from pypdfium2._exceptions import *
from pypdfium2 import _pypdfium as pdfium

logger = logging.getLogger(__name__)


class PdfContext:
    """
    Context manager to open (and automatically close again) a PDFium document
    from a file path.
    
    Parameters:
        
        file_path:
            File path string to a PDF document.
        
        password:
            A password to unlock the document, if encrypted.
    
    Returns:
        ``FPDF_DOCUMENT``
    """
    
    # On Windows, FPDF_LoadDocument() does not support filenames with multi-byte characters
    # https://bugs.chromium.org/p/pdfium/issues/detail?id=682
    
    def __init__(self, file_path: str, password: Optional[str] = None):
        self.file_path = abspath(str(file_path))
        self.password = password
    
    def __enter__(self) -> pdfium.FPDF_DOCUMENT:    
        
        self.pdf = pdfium.FPDF_LoadDocument(self.file_path, self.password)
        page_count = pdfium.FPDF_GetPageCount(self.pdf)
        
        if page_count < 1:
            
            last_error = pdfium.FPDF_GetLastError()
            if last_error == pdfium.FPDF_ERR_SUCCESS:
                raise LoadPdfError(f"Even though no errors were reported, page count is invalid.")
            elif last_error == pdfium.FPDF_ERR_UNKNOWN:
                raise LoadPdfError("An unknown error occurred whilst attempting to load the document.")
            elif last_error == pdfium.FPDF_ERR_FILE:
                raise LoadPdfError("The file could not be found or opened.")
            elif last_error == pdfium.FPDF_ERR_FORMAT:
                raise LoadPdfError("The file is not a PDF.")
            elif last_error == pdfium.FPDF_ERR_PASSWORD:
                raise LoadPdfError("Missing or wrong password.")
            elif last_error == pdfium.FPDF_ERR_SECURITY:
                raise LoadPdfError("The document uses an unsupported security scheme.")
            else:
                raise LoadPdfError(f"Unknown PDFium error code {last_error}.")
        
        return self.pdf
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        pdfium.FPDF_CloseDocument(self.pdf)


def _translate_rotation(rotation: int):
    if rotation == 0:
        return 0
    elif rotation == 90:
        return 1
    elif rotation == 180:
        return 2
    elif rotation == 270:
        return 3
    else:
        raise ValueError(f"Invalid rotation {rotation}")


def render_page(
        pdf: pdfium.FPDF_DOCUMENT,
        page_index: int,
        *,
        scale: float = 1,
        rotation: int = 0,
        background_colour: int = 0xFFFFFFFF,
        render_annotations: bool = True,
        optimise_mode: OptimiseMode = OptimiseMode.none,
    ) -> Image.Image:
    """
    Rasterise a PDF page using PDFium.
    
    Parameters:
        
        pdf:
            A PDFium document (can be obtained with :class:`PdfContext`).
        
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
        
        background_colour:
            
            .. _8888 ARGB: https://en.wikipedia.org/wiki/RGBA_color_model#ARGB32
            
            A 32-bit colour value in `8888 ARGB`_ format. Defaults to white (``0xFFFFFFFF``).
            To use an alpha channel rather than a background colour, set it to *None*.
        
        render_annotations:
            Whether to render page annotations.
        
        optimise_mode:
            Optimise rendering for LCD displays or for printing.
    
    Returns:
        :class:`PIL.Image.Image`
    """
    
    page_count = pdfium.FPDF_GetPageCount(pdf)
    if not 0 <= page_index < page_count:
        raise PageIndexError(f"Page index {page_index} is out of bounds for document with {page_count} pages.")
    
    page = pdfium.FPDF_LoadPage(pdf, page_index)
    
    width  = math.ceil(pdfium.FPDF_GetPageWidthF(page)  * scale)
    height = math.ceil(pdfium.FPDF_GetPageHeightF(page) * scale)
    
    if rotation in (90, 270):
        width, height = height, width
    
    if background_colour is None:
        bitmap = pdfium.FPDFBitmap_Create(width, height, 1)
    else:
        bitmap = pdfium.FPDFBitmap_Create(width, height, 0)
    
    if background_colour is not None:
        pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, background_colour)
    
    render_flags = 0x00
    if render_annotations:
        render_flags |= pdfium.FPDF_ANNOT
    
    if optimise_mode is OptimiseMode.none:
        pass
    elif optimise_mode is OptimiseMode.lcd_display:
        render_flags |= pdfium.FPDF_LCD_TEXT
    elif optimise_mode is OptimiseMode.printing:
        render_flags |= pdfium.FPDF_PRINTING
    else:
        raise ValueError(f"Invalid optimise_mode {optimise_mode}")
    
    pdfium.FPDF_RenderPageBitmap(
        bitmap,
        page,
        0, 0,
        width, height,
        _translate_rotation(rotation),
        render_flags,
    )
    
    cbuffer = pdfium.FPDFBitmap_GetBuffer(bitmap)
    buffer = ctypes.cast(cbuffer, ctypes.POINTER(ctypes.c_ubyte * (width * height * 4)))
    
    pil_image = Image.frombuffer("RGBA", (width, height), buffer.contents, "raw", "BGRA", 0, 1)
    
    if background_colour is not None:
        pil_image = pil_image.convert("RGB")
    
    if bitmap is not None:
        pdfium.FPDFBitmap_Destroy(bitmap)
    pdfium.FPDF_ClosePage(page)
    
    return pil_image


def _process_page(
        filename,
        index,
        password,
        scale,
        rotation,
        background_colour,
        render_annotations,
        optimise_mode,
    ) -> Image.Image:
    
    with PdfContext(filename, password) as pdf:
        pil_image = render_page(
            pdf, index,
            scale = scale,
            rotation = rotation,
            background_colour = background_colour,
            render_annotations = render_annotations,
            optimise_mode = optimise_mode,
        )
    
    return index, pil_image


def _invoke_process_page(args):
    return _process_page(*args)


def render_pdf(
        filename: str,
        page_indices: list = None,
        *,
        password: str = None,
        scale: float = 1,
        rotation: int = 0,
        background_colour: int = 0xFFFFFFFF,
        render_annotations: bool = True,
        optimise_mode: OptimiseMode = OptimiseMode.none,
        n_processes = os.cpu_count(),
    ):
    """
    Render certain pages of a PDF file, using a process pool executor.
    
    Parameters:
        
        filename:
            Path to a PDF file.
            (On Windows, a temporary copy is made if the path contains non-ascii characters.)
        
        page_indices:
            A list of zero-based page indices to render.
    
    The other parameters are the same as for :func:`render_page`.
    
    Yields:
        :class:`PIL.Image.Image`, and a suffix for serial enumeration of output files.
    """
    
    temporary = None
    if sys.platform.startswith('win32') and not filename.isascii():
        logger.warning(f"Using temporary copy {temporary.name} due to issues with non-ascii filenames on Windows.")
        temporary = tempfile.NamedTemporaryFile()
        with open(filename, 'rb') as file_handle:
            temporary.write(file_handle.read())
        filename = temporary.name
    
    with PdfContext(filename, password) as pdf:
        n_pages = pdfium.FPDF_GetPageCount(pdf)
    n_digits = len(str(n_pages))
    
    if page_indices is None or len(page_indices) == 0:
        page_indices = [i for i in range(n_pages)]
    elif any(i >= n_pages for i in page_indices):
        raise ValueError("Out of range page index detected.")
    
    meta_args = []
    for i in page_indices:
        sub_args = [
            filename,
            i,
            password,
            scale,
            rotation,
            background_colour,
            render_annotations,
            optimise_mode,
        ]
        meta_args.append(sub_args)
    
    with concurrent.futures.ProcessPoolExecutor(n_processes) as pool:
        for index, image in pool.map(_invoke_process_page, meta_args):
            pageno = index+1
            suffix = f"{pageno:0{n_digits}}"
            yield image, suffix
    
    if temporary is not None:
        temporary.close()
