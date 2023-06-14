# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PdfTextPage", "PdfTextSearcher")

import ctypes
import logging
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i
from pypdfium2._helpers.misc import PdfiumError

c_double = ctypes.c_double

logger = logging.getLogger(__name__)


class PdfTextPage (pdfium_i.AutoCloseable):
    """
    Text page helper class.
    
    Attributes:
        raw (FPDF_TEXTPAGE): The underlying PDFium textpage handle.
        page (PdfPage): Reference to the page this textpage belongs to.
    """
    
    def __init__(self, raw, page):
        self.raw = raw
        self.page = page
        super().__init__(pdfium_c.FPDFText_ClosePage)
    
    @property
    def parent(self):  # AutoCloseable hook
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
        
        # NOTE apparently, pdfium treats a surrogate pair like two separate chars, so this allocates enough memory and we end up with the right result
        # (which however is no good API design - pdfium should properly handle surrogation and the API should tell the exact amount of memory needed)
        n_bytes = count * 2
        buffer = ctypes.create_string_buffer(n_bytes+2)
        buffer_ptr = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ushort))
        
        pdfium_c.FPDFText_GetText(self, index, count, buffer_ptr)
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
        
        args = (self, left, top, right, bottom)
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
        n_chars = pdfium_c.FPDFText_CountChars(self)
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
        n_rects = pdfium_c.FPDFText_CountRects(self, index, count)
        if n_rects == -1:
            raise PdfiumError("Failed to count rectangles.")
        return n_rects
    
    
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
        index = pdfium_c.FPDFText_GetCharIndexAtPos(self, x, y, x_tol, y_tol)
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
                TODO
        Returns:
            Float values for left, bottom, right and top in PDF canvas units.
        """
        
        if loose:
            rect = pdfium_c.FS_RECTF()
            ok = pdfium_c.FPDFText_GetLooseCharBox(self, index, rect)
            l, b, r, t = rect.left, rect.bottom, rect.right, rect.top
        else:
            l, b, r, t = c_double(), c_double(), c_double(), c_double()
            ok = pdfium_c.FPDFText_GetCharBox(self, index, l, r, b, t)  # yes, lrbt!
            l, b, r, t = l.value, b.value, r.value, t.value
        
        if not ok:
            raise PdfiumError("Failed to get charbox.")
        
        return l, b, r, t
    
    
    def get_rect(self, index):
        """
        Get the bounding box of a text rectangle at the given index.
        Note that :meth:`.count_rects` must be called once with default parameters
        before subsequent :meth:`.get_rect` calls for this function to work (due to PDFium's API).
        
        Returns:
            Float values for left, bottom, right and top in PDF canvas units.
        """
        l, b, r, t = c_double(), c_double(), c_double(), c_double()
        ok = pdfium_c.FPDFText_GetRect(self, index, l, t, r, b)  # yes, ltrb!
        if not ok:
            raise PdfiumError("Failed to get rectangle. (Make sure count_rects() was called with default params once before subsequent get_rect() calls.)")
        return (l.value, b.value, r.value, t.value)
    
    
    def search(self, text, index=0, match_case=False, match_whole_word=False, consecutive=False):
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
            consecutive (bool):
                If False (the default), :meth:`.search` will skip past the current match to look for the next match.
                If True, parts of the previous match may be caught again (e. g. searching for `aa` in `aaaa` would match 3 rather than 2 times).
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
        if consecutive:
            flags |= pdfium_c.FPDF_CONSECUTIVE
        
        enc_text = (text + "\x00").encode("utf-16-le")
        enc_text_ptr = ctypes.cast(enc_text, ctypes.POINTER(ctypes.c_ushort))
        raw_searcher = pdfium_c.FPDFText_FindStart(self, enc_text_ptr, flags, index)
        searcher = PdfTextSearcher(raw_searcher, self)
        self._add_kid(searcher)
        return searcher


class PdfTextSearcher (pdfium_i.AutoCloseable):
    """
    Text searcher helper class.
    
    Attributes:
        raw (FPDF_SCHHANDLE): The underlying PDFium searcher handle.
        textpage (PdfTextPage): Reference to the textpage this searcher belongs to.
    """
    
    def __init__(self, raw, textpage):
        self.raw = raw
        self.textpage = textpage
        super().__init__(pdfium_c.FPDFText_FindClose)
    
    @property
    def parent(self):  # AutoCloseable hook
        return self.textpage
    
    
    def _get_occurrence(self, find_func):
        ok = find_func(self)
        if not ok:
            return None
        # FIXME what's the point of `count`? isn't it always equal to the length of the search text?
        index = pdfium_c.FPDFText_GetSchResultIndex(self)
        count = pdfium_c.FPDFText_GetSchCount(self)
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
