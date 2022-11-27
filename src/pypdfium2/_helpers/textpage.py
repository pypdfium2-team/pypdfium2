# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ["PdfTextPage", "PdfTextSearcher"]

import ctypes
import logging
import pypdfium2.raw as pdfium_c
from pypdfium2._helpers.misc import PdfiumError
from pypdfium2._helpers._internal.autoclose import AutoCloseable

c_double = ctypes.c_double

logger = logging.getLogger(__name__)


class PdfTextPage (AutoCloseable):
    """
    Text page helper class.
    
    Attributes:
        raw (FPDF_TEXTPAGE): The underlying PDFium textpage handle.
        page (PdfPage): Reference to the page this textpage belongs to.
    """
    
    def __init__(self, raw, page):
        self.raw = raw
        self.page = page
        AutoCloseable.__init__(self, pdfium_c.FPDFText_ClosePage)
    
    @property
    def parent(self):
        return self.page
    
    
    def get_text_range(self, index=0, count=-1, errors="ignore"):
        """
        Extract text from a given range.
        
        See `this benchmark <https://github.com/py-pdf/benchmarks>`_ for a performance and quality comparison with other tools.
        
        Parameters:
            index (int): Index of the first character to include.
            count (int): Number of characters to be extracted (defaults to -1 for all remaining characters after *index*).
            errors (str): Error treatment when decoding the data (see :meth:`bytes.decode`).
        Returns:
            str: The text in the range in question, or an empty string if no text was found.
        """
        
        if count == -1:
            count = self.count_chars() - index
        
        n_bytes = count * 2
        buffer = ctypes.create_string_buffer(n_bytes+2)
        buffer_ptr = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ushort))
        
        pdfium_c.FPDFText_GetText(self.raw, index, count, buffer_ptr)
        return buffer.raw[:n_bytes].decode("utf-16-le", errors=errors)
    
    
    def get_text_bounded(self, left=None, bottom=None, right=None, top=None, errors="ignore"):
        """
        Extract text from given boundaries in PDF coordinates.
        If a boundary value is None, it defaults to the corresponding value of :meth:`.PdfPage.get_bbox`.
        
        Parameters:
            errors (str): Error treatment when decoding the data (see :meth:`bytes.decode`).
        Returns:
            str: The text on the page area in question, or an empty string if no text was found.
        """
        
        bbox = self.page.get_bbox()
        if left is None:
            left = bbox[0]
        if bottom is None:
            bottom = bbox[1]
        if right is None:
            right = bbox[2]
        if top is None:
            top = bbox[3]
        
        args = (self.raw, left, top, right, bottom)
        n_chars = pdfium_c.FPDFText_GetBoundedText(*args, None, 0)
        if n_chars <= 0:
            return ""
        
        n_bytes = 2 * n_chars
        buffer = ctypes.create_string_buffer(n_bytes)
        buffer_ptr = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ushort))
        pdfium_c.FPDFText_GetBoundedText(*args, buffer_ptr, n_chars)
        return buffer.raw.decode("utf-16-le", errors=errors)
    
    
    def count_chars(self):
        """
        Returns:
            int: The number of characters on the text page.
        """
        n_chars = pdfium_c.FPDFText_CountChars(self.raw)
        if n_chars == -1:
            raise PdfiumError("Failed to get character count.")
        return n_chars
    
    
    def count_rects(self, index=0, count=-1):
        """
        Parameters:
            index (int): Start character index.
            count (int): Character count to consider (defaults to -1 for all remaining).
        Returns:
            int: The number of text rectangles in the given character range.
        """
        result = pdfium_c.FPDFText_CountRects(self.raw, index, count)
        if result == -1:
            raise PdfiumError("Failed to count rectangles.")
        return result
    
    
    def get_index(self, x, y, x_tol, y_tol):
        """
        Get the index of a character by position.
        
        Parameters:
            x (float): Horizontal position (in PDF canvas units).
            y (float): Vertical position.
            x_tol (float): Horizontal tolerance.
            y_tol (float): Vertical tolerance.
        Returns:
            int | None: The index of the character at or nearby the point (x, y).
            May be None if there is no character or an error occurred.
        """
        index = pdfium_c.FPDFText_GetCharIndexAtPos(self.raw, x, y, x_tol, y_tol)
        if index < 0:
            return None
        return index
    
    
    def get_charbox(self, index, loose=False):
        """
        Get the bounding box of a single character.
        
        Parameters:
            index (int):
                Index of the character to work with, in the page's character array.
            loose (bool):
                If True, the entire glyph bounds will be covered, without taking the actual glyph shape into account.
        Returns:
            Float values for left, bottom, right and top in PDF canvas units.
        """
        
        if loose:
            rect = pdfium_c.FS_RECTF()
            success = pdfium_c.FPDFText_GetLooseCharBox(self.raw, index, rect)
            left, bottom, right, top = rect.left, rect.bottom, rect.right, rect.top
        else:
            left, bottom, right, top = c_double(), c_double(), c_double(), c_double()
            success = pdfium_c.FPDFText_GetCharBox(self.raw, index, left, right, bottom, top)
            left, bottom, right, top = left.value, bottom.value, right.value, top.value
        
        if not success:
            raise PdfiumError("Failed to get charbox.")
        
        return left, bottom, right, top
    
    
    def get_rect(self, index):
        """
        Get the bounding box of a text rectangle at the given index.
        
        Returns:
            Float values for left, bottom, right and top in PDF canvas units.
        """
        left, top, right, bottom = c_double(), c_double(), c_double(), c_double()
        pdfium_c.FPDFText_GetRect(self.raw, index, left, top, right, bottom)
        return (left.value, bottom.value, right.value, top.value)
    
    
    def search(self, text, index=0, match_case=False, match_whole_word=False):
        """
        Locate text on the page.
        
        Parameters:
            text (str):
                The string to search for.
            index (int):
                Character index at which to start searching.
            match_case (bool):
                If True, the search will be case-specific (upper and lower letters treated as different characters).
            match_whole_word (bool):
                If True, substring occurrences will be ignored (e. g. `cat` would not match `category`).
        Returns:
            PdfTextSearcher: A helper object to search text.
        """
        
        if len(text) == 0:
            raise ValueError("Text length must be greater than 0.")
        
        flags = 0
        if match_case:
            flags |= pdfium_c.FPDF_MATCHCASE
        if match_whole_word:
            flags |= pdfium_c.FPDF_MATCHWHOLEWORD
        
        enc_text = (text + "\x00").encode("utf-16-le")
        enc_text_ptr = ctypes.cast(enc_text, ctypes.POINTER(ctypes.c_ushort))
        search = pdfium_c.FPDFText_FindStart(self.raw, enc_text_ptr, flags, index)
        return PdfTextSearcher(search, self)


class PdfTextSearcher (AutoCloseable):
    """
    Text searcher helper class.
    
    Attributes:
        raw (FPDF_SCHHANDLE): The underlying PDFium searcher handle.
        textpage (PdfTextPage): Reference to the textpage this searcher belongs to.
    """
    
    def __init__(self, raw, textpage):
        self.raw = raw
        self.textpage = textpage
        AutoCloseable.__init__(self, pdfium_c.FPDFText_FindClose)
    
    @property
    def parent(self):
        return self.textpage
    
    def _get_occurrence(self, find_func):
        success = find_func(self.raw)
        if not success:
            return None
        index = pdfium_c.FPDFText_GetSchResultIndex(self.raw)
        count = pdfium_c.FPDFText_GetSchCount(self.raw)
        return index, count
    
    def get_next(self):
        """
        Returns:
            (int, int): Start character index and count of the next occurrence,
            or None if the last occurrence was passed.
        """
        return self._get_occurrence(pdfium_c.FPDFText_FindNext)
    
    def get_prev(self):
        """
        Returns:
            (int, int): Start character index and count of the previous occurrence (i. e. the one before the last valid occurrence),
            or None if the last occurrence was passed.
        """
        return self._get_occurrence(pdfium_c.FPDFText_FindPrev)
