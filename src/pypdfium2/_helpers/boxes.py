# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from ctypes import c_float, byref
from pypdfium2 import _pypdfium as pdfium


def _get_box(page, box_function, fallback_function):
    
    left, bottom, right, top = c_float(), c_float(), c_float(), c_float()
    
    ret_code = box_function(page, byref(left), byref(bottom), byref(right), byref(top))
    if not ret_code:
        return fallback_function(page)
    
    return (left.value, bottom.value, right.value, top.value)


def get_mediabox(page):
    """
    Get the MediaBox of *page* in PDF canvas units (usually 1/72in).
    Falls back to ANSI A (0, 0, 612, 792) if the page does not define a MediaBox.
    
    Parameters:
        page (``FPDF_PAGE``): PDFium page object handle.
    
    Returns:
        A tuple of four float coordinates.
    """
    return _get_box(page, pdfium.FPDFPage_GetMediaBox, lambda _p: (0, 0, 612, 792))


def get_cropbox(page):
    """ Get the CropBox of *page* (Fallback: :func:`get_mediabox`) """
    return _get_box(page, pdfium.FPDFPage_GetCropBox, get_mediabox)

def get_bleedbox(page):
    """ Get the BleedBox of *page* (Fallback: :func:`get_cropbox`) """
    return _get_box(page, pdfium.FPDFPage_GetBleedBox, get_cropbox)

def get_trimbox(page):
    """ Get the TrimBox of *page* (Fallback: :func:`get_cropbox`) """
    return _get_box(page, pdfium.FPDFPage_GetTrimBox, get_cropbox)

def get_artbox(page):
    """ Get the ArtBox of *page* (Fallback: :func:`get_cropbox`) """
    return _get_box(page, pdfium.FPDFPage_GetArtBox, get_cropbox)
