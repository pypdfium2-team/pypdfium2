# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from ctypes import c_float
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.misc import PdfiumError


class PdfPageObject:
    """
    Page object helper class.
    
    Attributes:
        raw (FPDF_PAGEOBJECT):
            The underlying PDFium pageobject handle.
        page (PdfPage):
            Reference to the page this pageobject belongs to.
            If the object does not belong to a page yet, this parameter may be :data:`None`.
        pdf (PdfDocument):
            Reference to the document this pageobject belongs to.
            This parameter only needs to be given if *page* is :data:`None`.
        level (int):
            Nesting level signifying the number of parent Form XObjects. Zero if the object is not nested in a Form XObject.
        type (int):
            The type of the object (:data:`FPDF_PAGEOBJ_*`).
    """
    
    def __init__(self, raw, page=None, pdf=None, level=0):
        
        if all(o is not None for o in (page, pdf)):
            raise ValueError("*page* and *pdf* are mutually exclusive.")
        if all(o is None for o in (page, pdf)):
            raise ValueError("Either *page* or *pdf* needs to be given.")
        
        self.raw = raw
        self.page = page
        self.pdf = (page.pdf if pdf is None else pdf)
        self.level = level
        self.type = pdfium.FPDFPageObj_GetType(self.raw)
    
    
    def get_pos(self):
        """
        Get the position of the object on the page.
        
        Returns:
            A tuple of four :class:`float` coordinates for left, bottom, right, and top.
        """
        left, bottom, right, top = c_float(), c_float(), c_float(), c_float()
        ret_code = pdfium.FPDFPageObj_GetBounds(self.raw, left, bottom, right, top)
        if not ret_code:
            raise PdfiumError("Locating the page object failed")
        return (left.value, bottom.value, right.value, top.value)
    
    
    def get_matrix(self):
        pass  # TODO
    
    
    def set_matrix(self, matrix):
        pass  # TODO
    
    
    def transform(self, matrix):
        pass  # TODO
    
    
