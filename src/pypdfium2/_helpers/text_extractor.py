# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
from pypdfium2 import _pypdfium as pdfium


class PdfTextPage:
    """ Support model for PDF text extraction. """
    
    def __init__(self, page, close_input=False):
        self._page = page
        self._close_input = close_input
        self._textpage = pdfium.FPDFText_LoadPage(self._page)
        if not self._textpage:
            raise RuntimeError("Text page failed to load.")
    
    @property
    def raw(self):
        """ Get the raw PDFium ``FPDF_TEXTPAGE`` handle. """
        return self._textpage
    
    def close(self):
        """ Close the text page to release allocated memory. """
        pdfium.FPDFText_ClosePage(self._textpage)
        if self._close_input:
            pdfium.FPDF_ClosePage(self._page)
    
    def get_text(self, left=0, bottom=0, right=0, top=0):
        """
        Extract text from given boundaries. If *right* and/or *top* are 0, they default to page width or height, respectively.
        
        Returns:
            The text on the page area in question, or an empty string if no text was found.
        """
        
        width = pdfium.FPDF_GetPageWidthF(self._page)
        height = pdfium.FPDF_GetPageHeightF(self._page)
        if right == 0:
            right = width
        if top == 0:
            top = height
        
        if not (0 <= left < right <= width) or not (0 <= bottom < top <= height):
            raise ValueError("Invalid page area requested.")
        
        args = (self._textpage, left, top, right, bottom)
        n_chars = pdfium.FPDFText_GetBoundedText(*args, None, 0)
        if n_chars <= 0:
            return ""
        
        c_array = (ctypes.c_ushort * (n_chars+1))()
        pdfium.FPDFText_GetBoundedText(*args, ctypes.cast(c_array, ctypes.POINTER(ctypes.c_ushort)), n_chars)
        text = bytes(c_array).decode("utf-16-le")[:-1]
        
        return text
    
    def count_chars(self):
        """
        Returns the number of characters on the page.
        """
        return pdfium.FPDFText_CountChars(self._textpage)
    
    def count_rects(self, index=0, count=0):
        """
        Returns the number of text rectangles on the page.
        
        Parameters:
            index (int): Character index at which to start.
            count (int): Character count to consider (defaults to :meth:`.count_chars`).
        """
        n_chars = self.count_chars()
        if n_chars == 0:
            return 0
        if count == 0:
            count = n_chars
        if not (0 <= index < index+count <= n_chars):
            raise ValueError("Character span is out of bounds.")
        return pdfium.FPDFText_CountRects(self._textpage, index, count)
    
    def get_rects(self, index=0, count=0):
        """
        Get the bounding boxes of text rectangles in the requested scope.
        
        Yields:
            Coordinates for (left, bottom, right, top).
        """
        n_rects = self.count_rects(index, count)
        for index in range(n_rects):
            left, top, right, bottom = [ctypes.c_double() for _i in range(4)]
            pdfium.FPDFText_GetRect(self._textpage, index, *[ctypes.byref(coord) for coord in (left, top, right, bottom)])
            yield [coord.value for coord in (left, bottom, right, top)]
