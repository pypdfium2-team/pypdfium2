# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
from pypdfium2 import _pypdfium as pdfium


def get_pageobjs(page):
    """
    Get all page objects present on the given page.
    
    Yields:
        ``FPDF_PAGEOBJECT``
    """
    n_objects = pdfium.FPDFPage_CountObjects(page)
    for i in range(n_objects):
        yield pdfium.FPDFPage_GetObject(page, i)

def filter_pageobjs(page_objects, obj_type):
    """
    Get itmes of a certain type from a sequence of page objects.
    
    Parameters:
        obj_type (``FPDF_PAGEOBJ_...``):
            The object type to filter.
    Yields:
        ``FPDF_PAGEOBJECT``
    """
    for page_obj in page_objects:
        if pdfium.FPDFPageObj_GetType(page_obj) == obj_type:
            yield page_obj

def locate_pageobj(page_object):
    """
    Get the bounding box of a page object.
    
    Returns:
        Coordinates for (left, bottom, right, top).
    """
    left, bottom, right, top = [ctypes.c_float() for _ in range(4)]
    ret_code = pdfium.FPDFPageObj_GetBounds(page_object, *[ctypes.byref(coord) for coord in (left, bottom, right, top)])
    if not ret_code:
        raise RuntimeError("Locating the page object failed")
    return [coord.value for coord in (left, bottom, right, top)]
