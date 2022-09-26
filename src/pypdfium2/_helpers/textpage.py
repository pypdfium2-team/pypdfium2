# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
from ctypes import c_double
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.misc import PdfiumError


class PdfTextPage:
    """
    Text extraction helper class.
    
    Attributes:
        raw (FPDF_TEXTPAGE): The underlying PDFium textpage handle.
        page (PdfPage): Reference to the page this textpage belongs to.
    """
    
    def __init__(self, raw, page):
        self.raw = raw
        self.page = page
    
    def close(self):
        """
        Close the text page to release allocated memory.
        This method shall be called when finished working with the text page.
        """
        pdfium.FPDFText_ClosePage(self.raw)
        self.raw = None
    
    
    def get_text(self, left=0, bottom=0, right=0, top=0):
        """
        Extract text from given boundaries. If *right* and/or *top* are 0, they default to page width or height, respectively.
        
        See `this benchmark <https://github.com/py-pdf/benchmarks>`_ for a performance and quality comparison with other tools.
        
        Returns:
            str: The text on the page area in question, or an empty string if no text was found.
        """
        
        width, height = self.page.get_size()
        if right == 0:
            right = width
        if top == 0:
            top = height
        
        if not (0 <= left < right <= width) or not (0 <= bottom < top <= height):
            raise ValueError("Invalid page area requested.")
        
        args = (self.raw, left, top, right, bottom)
        n_chars = pdfium.FPDFText_GetBoundedText(*args, None, 0)
        if n_chars <= 0:
            return ""
        
        n_bytes = 2 * n_chars
        buffer = ctypes.create_string_buffer(n_bytes)
        buffer_ptr = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ushort))
        pdfium.FPDFText_GetBoundedText(*args, buffer_ptr, n_chars)
        text = buffer.raw.decode("utf-16-le", errors="ignore")
        
        return text
    
    
    def count_chars(self):
        """
        Returns:
            int: The number of characters on the page.
        """
        return pdfium.FPDFText_CountChars(self.raw)
    
    
    def count_rects(self, index=0, count=0):
        """
        Parameters:
            index (int): Character index at which to start.
            count (int): Character count to consider (defaults to :meth:`.count_chars`).
        Returns:
            int: The number of text rectangles on the page.
        """
        n_chars = self.count_chars()
        if n_chars == 0:
            return 0
        if count == 0:
            count = n_chars
        if not (0 <= index < index+count <= n_chars):
            raise ValueError("Character span is out of bounds.")
        return pdfium.FPDFText_CountRects(self.raw, index, count)
    
    
    def get_index(self, x, y, x_tol, y_tol):
        """
        Get the character index for a given position. All coordinates and lengths are to be given in PDF canvas units.
        
        Parameters:
            x (float): Horizontal position.
            y (float): Vertical position.
            x_tol (float): Horizontal tolerance.
            y_tol (float): Vertical tolerance.
        Returns:
            int | None: The index of the character at or nearby the point (x, y).
            May be :data:`None` if there is no character or an error occurred.
        """
        index = pdfium.FPDFText_GetCharIndexAtPos(self.raw, x, y, x_tol, y_tol)
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
            (float, float, float, float):
            Values for left, bottom, right and top in PDF canvas units.
        """
        
        n_chars = self.count_chars()
        if not 0 <= index < n_chars:
            raise ValueError("Character index %s is out of bounds. The maximum index is %d." % (index, n_chars-1))
        
        if loose:
            rect = pdfium.FS_RECTF()
            ret_code = pdfium.FPDFText_GetLooseCharBox(self.raw, index, rect)
            left, bottom, right, top = rect.left, rect.bottom, rect.right, rect.top
        else:
            left, bottom, right, top = c_double(), c_double(), c_double(), c_double()
            ret_code = pdfium.FPDFText_GetCharBox(self.raw, index, left, right, bottom, top)
            left, bottom, right, top = left.value, bottom.value, right.value, top.value
        
        if not ret_code:
            raise PdfiumError("Retrieving the char box failed")
        
        return left, bottom, right, top
    
    
    def get_rectboxes(self, index=0, count=0):
        """
        Get the bounding boxes of text rectangles in the requested scope.
        
        Yields:
            Coordinates for left, bottom, right, and top (as :class:`float` values).
        """
        n_rects = self.count_rects(index, count)
        for index in range(n_rects):
            left, top, right, bottom = c_double(), c_double(), c_double(), c_double()
            pdfium.FPDFText_GetRect(self.raw, index, left, top, right, bottom)
            yield (left.value, bottom.value, right.value, top.value)
    
    
    def get_links(self):
        """
        Iterate through web links on the page.
        
        Yields:
            :class:`str`: A web link string.
        """
        
        links = pdfium.FPDFLink_LoadWebLinks(self.raw)
        n_links = pdfium.FPDFLink_CountWebLinks(links)
        
        for i in range(n_links):
            n_chars = pdfium.FPDFLink_GetURL(links, i, None, 0)
            n_bytes = n_chars * 2
            buffer = ctypes.create_string_buffer(n_bytes)
            buffer_ptr = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ushort))
            pdfium.FPDFLink_GetURL(links, i, buffer_ptr, n_chars)
            yield buffer.raw[:n_bytes-2].decode("utf-16-le")
        
        pdfium.FPDFLink_CloseWebLinks(links)
    
    
    def search(self, text, index=0, match_case=False, match_whole_word=False):
        """
        Locate text on the page.
        
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
            PdfTextSearcher: A helper object to search text.
        """
        
        if len(text) == 0:
            raise ValueError("Text length must be >0.")
        
        flags = 0
        if match_case:
            flags |= pdfium.FPDF_MATCHCASE
        if match_whole_word:
            flags |= pdfium.FPDF_MATCHWHOLEWORD
        
        # assuming the pointer returned by ctypes.cast() keeps the casted object alive
        enc_text = (text + "\x00").encode("utf-16-le")
        enc_text_ptr = ctypes.cast(enc_text, ctypes.POINTER(ctypes.c_ushort))
        search = pdfium.FPDFText_FindStart(self.raw, enc_text_ptr, flags, index)
        return PdfTextSearcher(search, self)


class PdfTextSearcher:
    """
    Text searcher helper class.
    
    Attributes:
        raw (FPDF_SCHHANDLE): The underlying PDFium searcher handle.
        textpage (PdfTextPage): Reference to the textpage this searcher belongs to.
    """
    
    def __init__(self, raw, textpage):
        self.raw = raw
        self.textpage = textpage
    
    def close(self):
        """
        Close the search structure to release allocated memory.
        This method shall be called when done with text searching.
        """
        pdfium.FPDFText_FindClose(self.raw)
        self.raw = None
    
    def _get_occurrence(self, find_func):
        found = find_func(self.raw)
        if not found:
            return None
        index = pdfium.FPDFText_GetSchResultIndex(self.raw)
        count = pdfium.FPDFText_GetSchCount(self.raw)
        return tuple( [box for box in self.textpage.get_rectboxes(index, count)] )
    
    def get_next(self):
        """
        Returns:
            typing.Sequence[ typing.Tuple[float, float, float, float] ]:
            A list of bounding boxes for the next occurrence, or :data:`None` if the last occurrence was passed.
        """
        return self._get_occurrence(pdfium.FPDFText_FindNext)
    
    def get_prev(self):
        """
        Returns:
            typing.Sequence[ typing.Tuple[float, float, float, float] ]:
            A list of bounding boxes for the previous occurrence (i. e. the one before the last valid occurrence),
            or :data:`None` if the first occurrence was passed.
        """
        return self._get_occurrence(pdfium.FPDFText_FindPrev)
