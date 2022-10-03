# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from ctypes import c_float
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.misc import PdfiumError
from pypdfium2._helpers.matrix import PdfMatrix


class PdfPageObject:
    """
    Page object helper class.
    
    Attributes:
        raw (FPDF_PAGEOBJECT):
            The underlying PDFium pageobject handle.
        page (PdfPage):
            Reference to the page this pageobject belongs to. May be :data:`None` if the object does not belong to a page yet.
        pdf (PdfDocument):
            Reference to the document this pageobject belongs to. May be :data:`None` if the object does not belong to a document yet.
            This attribute is always set if :attr:`.page` is set.
        level (int):
            Nesting level signifying the number of parent Form XObjects. Zero if the object is not nested in a Form XObject.
        type (int):
            The type of the object (:data:`FPDF_PAGEOBJ_*`).
    """
    
    def __init__(self, raw, page=None, pdf=None, level=0):
        
        self.raw = raw
        self.page = page
        self.pdf = pdf
        self.level = level
        self.type = pdfium.FPDFPageObj_GetType(self.raw)
        
        if page is not None:
            if self.pdf is None:
                self.pdf = page.pdf
            elif self.pdf is not page.pdf:
                raise ValueError("*page* must belong to *pdf* when constructing a pageobject.")
    
    
    def get_pos(self):
        """
        Get the position of the object on the page.
        
        Returns:
            A tuple of four :class:`float` coordinates for left, bottom, right, and top.
        """
        if self.page is None:
            raise RuntimeError("Must not call get_pos() on a loose pageobject.")
        left, bottom, right, top = c_float(), c_float(), c_float(), c_float()
        ret_code = pdfium.FPDFPageObj_GetBounds(self.raw, left, bottom, right, top)
        if not ret_code:
            raise PdfiumError("Failed to locate pageobject.")
        return (left.value, bottom.value, right.value, top.value)
    
    
    def get_matrix(self):
        """
        Returns:
            PdfMatrix: The current matrix of the pageobject.
        """
        fs_matrix = pdfium.FS_MATRIX()
        success = pdfium.FPDFPageObj_GetMatrix(self.raw, fs_matrix)
        if not success:
            raise PdfiumError("Failed to get matrix of pageobject.")
        return PdfMatrix.from_pdfium(fs_matrix)
    
    
    def set_matrix(self, matrix):
        """
        Parameters:
            matrix (PdfMatrix): The new matrix the page object shall have.
        """
        if not isinstance(matrix, PdfMatrix):
            raise ValueError("*matrix* must be a PdfMatrix object.")
        success = pdfium.FPDFPageObj_SetMatrix(self.raw, matrix.to_pdfium())
        if not success:
            raise PdfiumError("Failed to set matrix of pageobject.")
    
    
    def transform(self, matrix):
        """
        Parameters:
            matrix (PdfMatrix): A matrix to be applied on top of existing transformations.
        """
        if not isinstance(matrix, PdfMatrix):
            raise ValueError("*matrix* must be a PdfMatrix object.")
        pdfium.FPDFPageObj_Transform(self.raw, *matrix.get())
    
    
