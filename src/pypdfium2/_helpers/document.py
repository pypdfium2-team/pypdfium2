# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import os
import os.path
import ctypes
import logging
import functools
from concurrent.futures import ProcessPoolExecutor

import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers._utils import ViewmodeMapping
from pypdfium2._helpers._opener import (
    open_pdf,
    is_input_buffer,
)
from pypdfium2._helpers.page import PdfPage
from pypdfium2._helpers.misc import (
    OutlineItem,
    raise_error,
    FileAccess,
)

try:
    import uharfbuzz as harfbuzz
except ImportError:
    have_harfbuzz = False
else:
    have_harfbuzz = True

logger = logging.getLogger(__name__)


class PdfDocument:
    """
    Document helper class.
    
    Parameters:
        input_data (str | bytes | typing.BinaryIO | FPDF_DOCUMENT):
            The input PDF given as file path, bytes, byte buffer, or raw PDFium document handle.
            A byte buffer is defined as an object that implements the methods ``seek()``, ``tell()`` and ``readinto()``.
        password (str | bytes):
            A password to unlock the PDF, if encrypted.
        autoclose (bool):
            If set to :data:`True` and a byte buffer was provided as input, :meth:`.close` will not only close the PDFium document, but also the input source.
        file_access (FileAccess):
            Define how files shall be opened internally. This parameter is ignored if *input_data* is not a file path.
    """
    
    def __init__(
            self,
            input_data,
            password = None,
            autoclose = False,
            file_access = FileAccess.NATIVE,
        ):
        
        self._orig_input = input_data
        self._actual_input = input_data
        self._rendering_input = None
        self._ld_data = None
        
        self._password = password
        self._autoclose = autoclose
        self._file_access = file_access
        
        if isinstance(self._orig_input, str):
            
            self._orig_input = os.path.abspath( os.path.expanduser(self._orig_input) )
            if not os.path.isfile(self._orig_input):
                raise FileNotFoundError("File does not exist: '%s'" % self._orig_input)
            
            if self._file_access is FileAccess.NATIVE:
                pass
            elif self._file_access is FileAccess.BUFFER:
                self._actual_input = open(self._orig_input, "rb")
                self._autoclose = True
            elif self._file_access is FileAccess.BYTES:
                buf = open(self._orig_input, "rb")
                self._actual_input = buf.read()
                buf.close()
            else:
                raise ValueError("An invalid file access strategy was given: '%s'" % self._file_access)
        
        if isinstance(self._actual_input, pdfium.FPDF_DOCUMENT):
            self._pdf = self._actual_input
        else:
            self._pdf, self._ld_data = open_pdf(self._actual_input, self._password, self._autoclose)
    
    @property
    def raw(self):
        """ FPDF_DOCUMENT: The raw PDFium document object handle. """
        return self._pdf
    
    @classmethod
    def new(cls):
        """
        Returns:
            PdfDocument: A new, empty document.
        """
        new_pdf = pdfium.FPDF_CreateNewDocument()
        return cls(new_pdf)
    
    def __len__(self):
        """ Get the document's number of pages (using :func:`len`) """
        return pdfium.FPDF_GetPageCount(self._pdf)
    
    def close(self):
        """
        Close the document to release allocated memory.
        This function shall be called when finished working with the object.
        """
        pdfium.FPDF_CloseDocument(self._pdf)
        if self._ld_data is not None:
            self._ld_data.close()
    
    
    def save(self, buffer, version=None):
        """
        Save the document into an output buffer, at its current state.
        
        Parameters:
            buffer (typing.BinaryIO):
                A byte buffer to capture the data.
                It may be any object implementing the ``write()`` method.
            version (typing.Optional[int]):
                 The PDF version to use, given as an integer (14 for 1.4, 15 for 1.5, ...).
                 If :data:`None`, PDFium will set a version automatically.
        """
        
        WriteFunctype = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(pdfium.FPDF_FILEWRITE), ctypes.POINTER(None), ctypes.c_ulong)
        
        filewrite = pdfium.FPDF_FILEWRITE()
        filewrite.WriteBlock = WriteFunctype( _writer_class(buffer) )
        
        saveargs = (self._pdf, ctypes.byref(filewrite), pdfium.FPDF_NO_INCREMENTAL)
        if version is None:
            success = pdfium.FPDF_SaveAsCopy(*saveargs)
        else:
            success = pdfium.FPDF_SaveWithVersion(*saveargs, version)
        
        if not success:
            raise_error("Saving the document failed")
    
    
    def _verify_index(self, index):
        n_pages = len(self)
        if not 0 <= index < n_pages:
            raise IndexError("Page index %s is out of bounds for document with %s pages." % (index, n_pages))
    
    def new_page(self, width, height, index=0):
        """
        Insert a new, empty page into the document.
        
        Parameters:
            width (float):
                Target page width (horizontal size).
            height (float):
                Target page height (vertical size).
            index (int):
                Suggested zero-based index at which the page will be inserted.
                If *index* is less or equal to zero, the page will be inserted at the beginning.
                If *index* is larger that the document's current last index, the page will be appended to the end.
        
        Returns:
            PdfPage: The newly created page.
        """
        raw_page = pdfium.FPDFPage_New(self._pdf, index, width, height)
        return PdfPage(raw_page, self)
    
    def del_page(self, index):
        """ Remove the page at *index*. """
        self._verify_index(index)
        pdfium.FPDFPage_Delete(self._pdf, index)
    
    def get_page(self, index):
        """
        Returns:
            PdfPage: The page at *index*.
        """
        self._verify_index(index)
        raw_page = pdfium.FPDF_LoadPage(self._pdf, index)
        return PdfPage(raw_page, self)
    
    
    def add_font(self, font_path, type, is_cid):
        """
        Add a font to the document.
        
        Parameters:
            font_path (str):
                File path of the font to use.
            type (int):
                A constant signifying the type of the given font (:data:`.FPDF_FONT_TYPE1` or :data:`.FPDF_FONT_TRUETYPE`).
            is_cid (bool):
                State whether the given font is a CID font or not.
        Returns:
            PdfFont: A font helper object.
        """
        
        with open(font_path, "rb") as fh:
            font_data = fh.read()
        
        pdf_font = pdfium.FPDFText_LoadFont(
            self._pdf,
            ctypes.cast(font_data, ctypes.POINTER(ctypes.c_uint8)),
            len(font_data),
            type,
            is_cid,
        )
        
        return PdfFont(pdf_font, font_data)
    
    
    def _get_bookmark(self, bookmark, level):
        
        t_buflen = pdfium.FPDFBookmark_GetTitle(bookmark, None, 0)
        t_buffer = ctypes.create_string_buffer(t_buflen)
        pdfium.FPDFBookmark_GetTitle(bookmark, t_buffer, t_buflen)
        title = t_buffer.raw[:t_buflen].decode('utf-16-le')[:-1]
        
        is_closed = pdfium.FPDFBookmark_GetCount(bookmark) < 0
        dest = pdfium.FPDFBookmark_GetDest(self._pdf, bookmark)
        page_index = pdfium.FPDFDest_GetDestPageIndex(self._pdf, dest)
        
        n_params = ctypes.c_ulong()
        view_pos = (pdfium.FS_FLOAT * 4)()
        view_mode = pdfium.FPDFDest_GetView(dest, n_params, view_pos)
        view_pos = list(view_pos)[:n_params.value]
        
        return OutlineItem(
            level = level,
            title = title,
            is_closed = is_closed,
            page_index = page_index,
            view_mode = view_mode,
            view_pos = view_pos,
        )
    
    
    def get_toc(
            self,
            max_depth = 15,
            parent = None,
            level = 0,
            seen = None,
        ):
        """
        Read the document's outline ("table of contents").
        
        Parameters:
            max_depth (int):
                Maximum recursion depth to consider when reading the outline.
        Yields:
            :class:`.OutlineItem`: The data of an outline item ("bookmark").
        """
        
        if level >= max_depth:
            return []
        if seen is None:
            seen = set()
        
        bookmark = pdfium.FPDFBookmark_GetFirstChild(self._pdf, parent)
        
        while bookmark:
            
            address = ctypes.addressof(bookmark.contents)
            if address in seen:
                logger.warning("A circular bookmark reference was detected whilst parsing the table of contents.")
                break
            else:
                seen.add(address)
            
            yield self._get_bookmark(bookmark, level)
            yield from self.get_toc(
                max_depth = max_depth,
                parent = bookmark,
                level = level + 1,
                seen = seen,
            )
            
            bookmark = pdfium.FPDFBookmark_GetNextSibling(self._pdf, bookmark)
    
    
    @staticmethod
    def print_toc(toc, n_digits=2):
        """
        Print a table of contents.
        
        Parameters:
            toc (typing.Iterator[OutlineItem]):
                Sequence of outline items to show.
            n_digits (int):
                The number of digits to which viewport coordinates shall be rounded.
        """
        
        for item in toc:
            print(
                '    ' * item.level +
                '[{}] '.format('-' if item.is_closed else '+') +
                '{} -> {}  # {} {}'.format(
                    item.title,
                    item.page_index+1,
                    ViewmodeMapping[item.view_mode],
                    [round(c, n_digits) for c in item.view_pos],
                )
            )
    
    
    def update_rendering_input(self):
        """
        Update the input sources for concurrent rendering to the document's current state
        by saving to bytes and setting the result as new input.
        If you modified the document, you may want to call this method before :meth:`._render_base`.
        """
        buffer = io.BytesIO()
        self.save(buffer)
        buffer.seek(0)
        self._rendering_input = buffer.read()
        buffer.close()
    
    
    @classmethod
    def _process_page(cls, index, renderer_name, input_data, password, file_access, **kwargs):
        pdf = cls(
            input_data,
            password = password,
            file_access = file_access,
        )
        page = pdf.get_page(index)
        result = getattr(page, "render_to"+renderer_name)(**kwargs)
        [g.close() for g in (page, pdf)]
        return result, index
    
    
    def _render_base(
            self,
            renderer_name,
            page_indices = None,
            n_processes = os.cpu_count(),
            **kwargs
        ):
        """
        Concurrently render multiple pages, using a process pool executor.
        This method serves as base for :meth:`.render_tobytes` and :meth:`render_topil`. Embedders should never call it directly.
        
        The order of results matches the order of given page indices.
        
        Parameters:
            page_indices (typing.Optional[typing.Sequence[int]]):
                A sequence of zero-based indices of the pages to render.
                If :data:`None`, all pages will be included.
            n_processes (int):
                Target number of parallel processes.
            kwargs (dict):
                Keyword arguments to be passed to :meth:`.PdfPage.render_base`.
        Yields:
            :data:`typing.Any`: Implementation-specific result object.
        """
        
        if self._rendering_input is None:
            if isinstance(self._orig_input, pdfium.FPDF_DOCUMENT):
                logger.warning("Cannot perform concurrent processing without input sources - saving the document implicitly to get picklable data.")
                self.update_rendering_input()
            elif is_input_buffer(self._orig_input):
                logger.warning("Cannot perform concurrent rendering with buffer input - reading the whole buffer into memory implicitly.")
                self._orig_input.seek(0)
                self._rendering_input = self._orig_input.read()
            else:
                self._rendering_input = self._orig_input
        
        n_pages = len(self)
        
        if page_indices is None or len(page_indices) == 0:
            page_indices = [i for i in range(n_pages)]
        if not all(0 <= i < n_pages for i in page_indices):
            raise ValueError("A page index is out of bounds.")
        
        invoke_renderer = functools.partial(
            PdfDocument._process_page,
            renderer_name = renderer_name,
            input_data = self._rendering_input,
            password = self._password,
            file_access = self._file_access,
            **kwargs
        )
        
        i = 0
        with ProcessPoolExecutor(n_processes) as pool:
            for result, index in pool.map(invoke_renderer, page_indices):
                assert index == page_indices[i]
                i += 1
                yield result
        
        assert len(page_indices) == i
    
    
    def render_tobytes(self, **kwargs):
        """
        Concurrently render pages to bytes.
        See :meth:`.PdfDocument._render_base` and :meth:`.PdfPage.render_base` for possible keyword arguments.
        
        Yields:
            :class:`tuple`: Result of :meth:`.PdfPage.render_tobytes`.
        """
        yield from self._render_base("bytes", **kwargs)
    
    def render_topil(self, **kwargs):
        """
        *Requires* :mod:`PIL`.
        
        Concurrently render pages to PIL images.
        See :meth:`.PdfDocument._render_base` and :meth:`.PdfPage.render_base` for possible keyword arguments.
        
        Yields:
            :class:`PIL.Image.Image`: PIL image.
        """
        yield from self._render_base("pil", **kwargs)


class _writer_class:
    
    def __init__(self, buffer):
        self.buffer = buffer
        if not callable( getattr(self.buffer, "write", None) ):
            raise ValueError("Output buffer must implement the write() method.")
    
    def __call__(self, _, data, size):
        block = ctypes.cast(data, ctypes.POINTER(ctypes.c_ubyte * size))
        self.buffer.write(block.contents)
        return 1


class HarfbuzzFont:
    """ Harfbuzz font data helper class. """
    
    def __init__(self, font_path):
        if not have_harfbuzz:
            raise RuntimeError("Font helpers require uharfbuzz to be installed.")
        self.blob = harfbuzz.Blob.from_file_path(font_path)
        self.face = harfbuzz.Face(self.blob)
        self.font = harfbuzz.Font(self.face)
        self.scale = self.font.scale[0]


class PdfFont:
    """ PDF font data helper class. """
    
    def __init__(self, pdf_font, font_data):
        self._pdf_font = pdf_font
        self._font_data = font_data
    
    @property
    def raw(self):
        """ FPDF_FONT: The raw PDFium font object handle. """
        return self._pdf_font
    
    def close(self):
        """
        Close the font to release allocated memory.
        This function shall be called when finished working with the object.
        """
        pdfium.FPDFFont_Close(self._pdf_font)
        id(self._font_data)
