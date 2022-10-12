# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
import weakref
import logging
from ctypes import c_double
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.misc import PdfiumError

logger = logging.getLogger(__name__)


class PdfTextPage:
    """
    Text page helper class.
    
    Attributes:
        raw (FPDF_TEXTPAGE): The underlying PDFium textpage handle.
        page (PdfPage): Reference to the page this textpage belongs to.
        n_chars (int): Number of characters on the page, at the time of initialisation.
    """
    
    def __init__(self, raw, page):
        self.raw = raw
        self.page = page
        self._finalizer = weakref.finalize(
            self, self._static_close,
            self.raw, self.page,
        )
        self.n_chars = pdfium.FPDFText_CountChars(self.raw)
    
    def _tree_closed(self):
        if self.raw is None:
            return True
        return self.page._tree_closed()
    
    @staticmethod
    def _static_close(raw, parent):
        # logger.debug("Closing text page")
        if parent._tree_closed():
            logger.critical("Some parent closed before text page (this is illegal). Direct parent: %s" % parent)
        pdfium.FPDFText_ClosePage(raw)
    
    def close(self):
        """
        Free memory by applying the finalizer for the underlying PDFium text page.
        Please refer to the generic note on ``close()`` methods for details.
        """
        if self.raw is None:
            logger.warning("Duplicate close call suppressed on text page %s" % self)
            return
        self._finalizer()
        self.raw = None
    
    
    def count_chars(self):
        """
        Deprecated alias for :attr:`.n_chars`. Will be removed with the next major release.
        """
        return self.n_chars
    
    
    @staticmethod
    def _check_span(n_chars, index, count):
        if not (0 <= index < index+count <= n_chars):
            raise ValueError("Character span is out of bounds.")
    
    
    def get_text_range(self, index=0, count=0, errors="ignore"):
        """
        Extract text from a given range.
        
        See `this benchmark <https://github.com/py-pdf/benchmarks>`_ for a performance and quality comparison with other tools.
        
        Parameters:
            index (int): Index of the first character to include.
            count (int): Number of characters to be extracted. If 0, it defaults to the number of characters on the page minus *index*.
            errors (str): Error treatment when decoding the data (see :meth:`bytes.decode`).
        Returns:
            str: The text in the range in question, or an empty string if no text was found.
        """
        
        if self.n_chars == 0:
            return ""
        if count == 0:
            count = self.n_chars - index
        self._check_span(self.n_chars, index, count)
        
        n_bytes = count * 2
        buffer = ctypes.create_string_buffer(n_bytes+2)
        buffer_ptr = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ushort))
        pdfium.FPDFText_GetText(self.raw, index, count, buffer_ptr)
        return buffer.raw[:n_bytes].decode("utf-16-le", errors=errors)
    
    
    def get_text_bounded(self, left=None, bottom=None, right=None, top=None, errors="ignore"):
        """
        Extract text from given boundaries in PDF coordinates.
        If a parameter is :data:`None`, it defaults to the corresponding CropBox value.
        
        Parameters:
            errors (str): Error treatment when decoding the data (see :meth:`bytes.decode`).
        Returns:
            str: The text on the page area in question, or an empty string if no text was found.
        """
        
        if self.n_chars == 0:
            return ""
        
        cropbox = self.page.get_cropbox()
        if left is None:
            left = cropbox[0]
        if bottom is None:
            bottom = cropbox[1]
        if right is None:
            right = cropbox[2]
        if top is None:
            top = cropbox[3]
        
        args = (self.raw, left, top, right, bottom)
        n_chars = pdfium.FPDFText_GetBoundedText(*args, None, 0)
        if n_chars <= 0:
            return ""
        
        n_bytes = 2 * n_chars
        buffer = ctypes.create_string_buffer(n_bytes)
        buffer_ptr = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ushort))
        pdfium.FPDFText_GetBoundedText(*args, buffer_ptr, n_chars)
        return buffer.raw.decode("utf-16-le", errors=errors)
    
    
    def get_text(self, *args, **kwargs):
        """
        Deprecated alias for :meth:`.get_text_bounded`. Will be removed with the next major release.
        """
        return self.get_text_bounded(*args, **kwargs)
    
    
    def count_rects(self, index=0, count=0):
        """
        Parameters:
            index (int): Character index at which to start.
            count (int): Character count to consider (defaults to :meth:`.count_chars`).
        Returns:
            int: The number of text rectangles on the page.
        """
        
        if self.n_chars == 0:
            return 0
        if count == 0:
            count = self.n_chars
        self._check_span(self.n_chars, index, count)
        
        return pdfium.FPDFText_CountRects(self.raw, index, count)
    
    
    def get_index(self, x, y, x_tol, y_tol):
        """
        Get the character index for a given position.
        
        Parameters:
            x (float): Horizontal position (in PDF canvas units).
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
        
        if not 0 <= index < self.n_chars:
            raise ValueError("Character index %s is out of bounds. The maximum index is %d." % (index, self.n_chars-1))
        
        if loose:
            rect = pdfium.FS_RECTF()
            success = pdfium.FPDFText_GetLooseCharBox(self.raw, index, rect)
            left, bottom, right, top = rect.left, rect.bottom, rect.right, rect.top
        else:
            left, bottom, right, top = c_double(), c_double(), c_double(), c_double()
            success = pdfium.FPDFText_GetCharBox(self.raw, index, left, right, bottom, top)
            left, bottom, right, top = left.value, bottom.value, right.value, top.value
        
        if not success:
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
        self._finalizer = weakref.finalize(
            self, self._static_close,
            self.raw, self.textpage,
        )
    
    def _tree_closed(self):
        if self.raw is None:
            return True
        return self.textpage._tree_closed()
    
    @staticmethod
    def _static_close(raw, parent):
        # logger.debug("Closing text searcher")
        if parent._tree_closed():
            logger.critical("Some parent closed before text searcher (this is illegal). Direct parent: %s" % parent)
        pdfium.FPDFText_FindClose(raw)
    
    def close(self):
        """
        Free memory by applying the finalizer for the underlying PDFium text searcher.
        Please refer to the generic note on ``close()`` methods for details.
        """
        if self.raw is None:
            logger.warning("Duplicate close call suppressed on text searcher %s" % self)
            return
        self._finalizer()
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
