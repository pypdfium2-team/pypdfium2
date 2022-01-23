# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from ctypes import c_float, byref
from typing import Tuple, Callable
from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers.error_handler import *


def _get_box(
        page: pdfium.FPDF_PAGE,
        box_function: Callable,
        fallback_function: Callable,
    ) -> Tuple[float]:
        
    left, bottom, right, top = c_float(), c_float(), c_float(), c_float()
    
    ret_code = box_function(
        page,
        byref(left), byref(bottom), byref(right), byref(top),
    )
    if not ret_code:
        return fallback_function(page)
    
    return (left.value, bottom.value, right.value, top.value)


def get_mediabox(page: pdfium.FPDF_PAGE) -> Tuple[float]:
    """
    Returns the MediaBox of *page* in PDF canvas units (usually 1/72in).
    Falls back to ANSI A if the page does not define a MediaBox.
    """
    
    return _get_box(
        page,
        pdfium.FPDFPage_GetMediaBox,
        lambda _page: (0, 0, 612, 792),
    )


def get_cropbox(page: pdfium.FPDF_PAGE) -> Tuple[float]:
    """
    Returns the CropBox of *page* in PDF canvas units (usually 1/72in).
    Falls back to MediaBox if the page does not define a CropBox.
    """
    
    return _get_box(
        page,
        pdfium.FPDFPage_GetCropBox,
        get_mediabox,
    )
