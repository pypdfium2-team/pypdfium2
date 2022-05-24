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
        """ Returns the number of characters on the page. """
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
    
    
    def get_index(self, x, y, x_tol, y_tol):
        """
        Get the character index for a given position. All coordinates and lengths are to be given in PDF canvas units.
        
        Parameters:
            x (int|float): Horizontal position.
            y (int|float): Vertical position.
            x_tol (int|float): Horizontal tolerance.
            y_tol (int|float): Vertical tolerance.
        
        Returns:
            The index (:class:`int`) of the character at or nearby the point (x, y).
            Returns :data:`None` if there is no character or an error occurred.
        """
        index = pdfium.FPDFText_GetCharIndexAtPos(self._textpage, x, y, x_tol, y_tol)
        if index < 0:
            return None
        return index
    
    
    def get_charbox(self, index, loose=False):
        """
        Get the bounding box of a single character.
        
        Parameters:
            index (int):
                Slot of the character to work with, in the page's character array.
            loose (bool):
                If True, the entire glyph bounds will be covered, without taking the actual glyph shape into account.
        
        Returns:
            Values for left, bottom, right and top in PDF canvas units.
        """
        
        n_chars = self.count_chars()
        if not 0 <= index < n_chars:
            raise ValueError("Character index %s is out of bounds. The maximum index is %d." % (index, n_chars-1))
        
        if loose:
            rect = pdfium.FS_RECTF()
            ret_code = pdfium.FPDFText_GetLooseCharBox(self._textpage, index, rect)
            left, bottom, right, top = rect.left, rect.bottom, rect.right, rect.top
        else:
            left, bottom, right, top = [ctypes.c_double() for _ in range(4)]
            ret_code = pdfium.FPDFText_GetCharBox(self._textpage, index, left, right, bottom, top)
            left, bottom, right, top = [item.value for item in (left, bottom, right, top)]
        
        if not ret_code:
            raise RuntimeError("Retrieving the char box failed.")
        
        return left, bottom, right, top
    
    
    def get_rectboxes(self, index=0, count=0):
        """
        Get the bounding boxes of text rectangles in the requested scope.
        
        Yields:
            Coordinates for (left, bottom, right, top).
        """
        n_rects = self.count_rects(index, count)
        for index in range(n_rects):
            left, top, right, bottom = [ctypes.c_double() for _ in range(4)]
            pdfium.FPDFText_GetRect(self._textpage, index, *[ctypes.byref(coord) for coord in (left, top, right, bottom)])
            yield [coord.value for coord in (left, bottom, right, top)]
    
    
    def search(self, text, index=0, match_case=False, match_whole_word=False):
        """
        Get a helper object to locate text on the page.
        
        Parameters:
            text (str):
                The string to search for.
            index (int):
                Character index at which to start searching.
            match_case (bool):
                If :data:`True`, the search will be case-specific (upper and lower letters treated as different characters).
            match_whole_word (bool):
                If :data:`True`, substring occurrences will be ignored (e. g. `cat` would not match `category`).
        Returns:
            :class:`.TextSearcher`
        """
        
        if len(text) == 0:
            raise ValueError("Text length must be >0.")
        
        flags = 0
        if match_case:
            flags |= pdfium.FPDF_MATCHCASE
        if match_whole_word:
            flags |= pdfium.FPDF_MATCHWHOLEWORD
        
        enc_text = text.encode("utf-16-le") + b"\x00\x00"
        text_pointer = ctypes.cast(enc_text, ctypes.POINTER(ctypes.c_uint16))
        search = pdfium.FPDFText_FindStart(self._textpage, text_pointer, flags, index)
        return TextSearcher(self, search)
        

class TextSearcher:
    """ Helper class to search text. """
    
    def __init__(self, textpage, search):
        self._textpage = textpage
        self._search = search
    
    def _get_occurrence(self, find_func):
        found = find_func(self._search)
        if not found:
            return None
        index = pdfium.FPDFText_GetSchResultIndex(self._search)
        count = pdfium.FPDFText_GetSchCount(self._search)
        return [box for box in self._textpage.get_rectboxes(index, count)]
    
    def get_next(self):
        """ Get a list of bounding boxes for the next occurrence. Returns :data:`None` if the last occurrence was passed. """
        return self._get_occurrence(pdfium.FPDFText_FindNext)
    
    def get_prev(self):
        """
        Get a list of bounding boxes for the previous occurrence (i. e. the one before the last valid occurrence).
        Returns :data:`None` if the first occurrence was passed.
        """
        return self._get_occurrence(pdfium.FPDFText_FindPrev)
    
    def close(self):
        """ Close the search structure to release allocated memory. It is mandatory to call this method when finished. """
        pdfium.FPDFText_FindClose(self._search)
