# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import os
import os.path
import weakref
import ctypes
import logging
import functools
from concurrent.futures import ProcessPoolExecutor

import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.misc import (
    OutlineItem,
    FileAccess,
    PdfiumError,
    ErrorToStr,
    ViewmodeToStr,
    get_functype,
    get_fileaccess,
    is_input_buffer,
)
from pypdfium2._helpers.pageobject import (
    PdfPageObject,
)
from pypdfium2._helpers.converters import BitmapConvAliases
from pypdfium2._helpers.page import PdfPage

try:
    import uharfbuzz as harfbuzz
except ImportError:
    harfbuzz = None

logger = logging.getLogger(__name__)


class PdfDocument (BitmapConvAliases):
    """
    Document helper class.
    
    Parameters:
        input_data (str | bytes | typing.BinaryIO | FPDF_DOCUMENT):
            The input PDF given as file path, bytes, byte buffer, or raw PDFium document handle.
            :func:`.is_input_buffer` defines which objects are recognised as byte buffers.
        password (str | bytes):
            A password to unlock the PDF, if encrypted.
            If the document is not encrypted but a password was given, PDFium will ignore it.
        file_access (FileAccess):
            This parameter may be used to control how files are opened internally. It is ignored if *input_data* is not a file path.
        autoclose (bool):
            If set to :data:`True` and a byte buffer was provided as input, :meth:`.close` will not only close the PDFium document, but also the input source.
    
    Raises:
        PdfiumError: Raised if the document failed to load. The exception message is annotated with the reason reported by PDFium.
        FileNotFoundError: Raised if an invalid or non-existent file path was given.
    
    Hint:
        * :func:`len` may be called to get a document's number of pages.
        * Looping over a document will yield its pages from beginning to end.
        * Pages may be loaded using list index access.
        * The ``del`` keyword and list index access may be used to delete pages.
    
    Attributes:
        raw (FPDF_DOCUMENT): The underlying PDFium document handle.
    """
    
    def __init__(
            self,
            input_data,
            password = None,
            file_access = FileAccess.NATIVE,
            autoclose = False,
        ):
        
        self._orig_input = input_data
        self._actual_input = input_data
        self._data_holder = []
        self._data_closer = []
        self._rendering_input = None
        
        self._password = password
        self._file_access = file_access
        self._autoclose = autoclose
        
        self._form_env = None
        self._form_config = None
        self._form_finalizer = None
        
        if isinstance(self._orig_input, str):
            
            self._orig_input = os.path.abspath( os.path.expanduser(self._orig_input) )
            if not os.path.isfile(self._orig_input):
                raise FileNotFoundError("File does not exist: '%s'" % self._orig_input)
            
            if self._file_access is FileAccess.NATIVE:
                pass
            elif self._file_access is FileAccess.BUFFER:
                self._actual_input = open(self._orig_input, "rb")
                self._data_closer.append(self._actual_input)
            elif self._file_access is FileAccess.BYTES:
                buf = open(self._orig_input, "rb")
                self._actual_input = buf.read()
                buf.close()
            else:
                assert False
        
        if isinstance(self._actual_input, pdfium.FPDF_DOCUMENT):
            self.raw = self._actual_input
        else:
            self.raw, ld_data = _open_pdf(self._actual_input, self._password)
            self._data_holder += ld_data
        
        if self._autoclose and is_input_buffer(self._actual_input):
            self._data_closer.append(self._actual_input)
        
        self._finalizer = weakref.finalize(
            self, self._static_close,
            self.raw, self._data_holder, self._data_closer,
        )
    
    
    def __enter__(self):
        return self
    
    def __exit__(self, *_):
        # We do not invoke close at this place anymore because that would increase the risk of callers closing parent objects before child objects.
        # (Consider a `with`-block where pages are not closed explicitly: garbage collection of pages commonly happens later than context manager exit, so page would be closed after document, which is illegal.)
        pass
    
    def __len__(self):
        return pdfium.FPDF_GetPageCount(self.raw)
    
    def __iter__(self):
        for i in range( len(self) ):
            yield self.get_page(i)
    
    def __getitem__(self, i):
        return self.get_page(i)
    
    def __delitem__(self, i):
        self.del_page(i)
    
    
    @classmethod
    def new(cls):
        """
        Returns:
            PdfDocument: A new, empty document.
        """
        new_pdf = pdfium.FPDF_CreateNewDocument()
        return cls(new_pdf)
    
    
    @staticmethod
    def _static_close(raw, data_holder, data_closer):
        
        # logger.debug("Closing document")
        pdfium.FPDF_CloseDocument(raw)
        
        for data in data_holder:
            id(data)
        for data in data_closer:
            data.close()
    
    
    @staticmethod
    def _static_exit_formenv(form_env, form_config):
        # logger.debug("Closing form env")
        pdfium.FPDFDOC_ExitFormFillEnvironment(form_env)
        id(form_config)
    
    
    def close(self):
        """
        Free memory by applying the finalizer for the underlying PDFium document.
        Please refer to the generic note on ``close()`` methods for details.
        
        This method calls :meth:`.exit_formenv`.
        """
        if self.raw is None:
            logger.warning("Duplicate close call suppressed on document %s" % self)
            return
        self.exit_formenv()
        self._finalizer()
        self.raw = None
        self._data_holder = []
        self._data_closer = []
    
    
    def _tree_closed(self):
        return (self.raw is None)
    
    
    def init_formenv(self):
        """
        Initialise a form environment handle for this document.
        If already initialised, the existing one will be returned instead.
        
        Returns:
            FPDF_FORMHANDLE:
        """
        if self._form_env is not None:
            return self._form_env
        self._form_config = pdfium.FPDF_FORMFILLINFO()
        self._form_config.version = 2
        self._form_env = pdfium.FPDFDOC_InitFormFillEnvironment(self.raw, self._form_config)
        self._form_finalizer = weakref.finalize(
            self, self._static_exit_formenv,
            self._form_env, self._form_config,
        )
        return self._form_env
    
    
    def exit_formenv(self):
        """
        Free memory by applying the finalizer for the underlying PDFium form environment, if it was initialised.
        If :meth:`.init_formenv` was not called, nothing will be done.
        
        This behaves like the ``close()`` methods. Please refer to the generic note for details.
        """
        if self._form_env is None:
            return
        self._form_finalizer()
        self._form_env = None
        self._form_config = None
    
    
    def get_version(self):
        """
        Returns:
            int | None: The PDF version of the document (14 for 1.4, 15 for 1.5, ...),
            or :data:`None` if the version could not be determined (e. g. because the document was created using :meth:`PdfDocument.new`).
        """
        version = ctypes.c_int()
        success = pdfium.FPDF_GetFileVersion(self.raw, version)
        if not success:
            return
        return int(version.value)
    
    
    def save(self, buffer, version=None):
        """
        Save the document into an output buffer, at its current state.
        
        Parameters:
            buffer (typing.BinaryIO):
                A byte buffer to capture the data.
                It may be any object implementing the ``write()`` method.
            version (int | None):
                 The PDF version to use, given as an integer (14 for 1.4, 15 for 1.5, ...).
                 If :data:`None`, PDFium will set a version automatically.
        """
        
        filewrite = pdfium.FPDF_FILEWRITE()
        filewrite.version = 1
        filewrite.WriteBlock = get_functype(pdfium.FPDF_FILEWRITE, "WriteBlock")( _writer_class(buffer) )
        
        saveargs = (self.raw, filewrite, pdfium.FPDF_NO_INCREMENTAL)
        if version is None:
            success = pdfium.FPDF_SaveAsCopy(*saveargs)
        else:
            success = pdfium.FPDF_SaveWithVersion(*saveargs, version)
        
        if not success:
            raise PdfiumError("Saving the document failed")
    
    
    def _handle_index(self, index):
        n_pages = len(self)
        if index < 0:
            index += n_pages
        if not 0 <= index < n_pages:
            raise IndexError("Page index %s is out of bounds for document with %s pages." % (index, n_pages))
        return index
    
    
    def get_page_size(self, index):
        """
        Get the dimensions of the page at *index*. Reverse indexing is allowed.
        
        Returns:
            (float, float): Page width and height in PDF canvas units.
        """
        index = self._handle_index(index)
        size = pdfium.FS_SIZEF()
        success = pdfium.FPDF_GetPageSizeByIndexF(self.raw, index, size)
        if not success:
            raise PdfiumError("Getting page size by index failed.")
        return (size.width, size.height)
    
    
    def page_as_xobject(self, index, dest_pdf):
        """
        Capture a page as XObject and attach it to a document's resources.
        
        Parameters:
            index (int): Zero-based index of the page. Reverse indexing is allowed.
            dest_pdf (PdfDocument): Target document to which the XObject shall be added.
        Returns:
            PdfXObject: The page as XObject.
        """
        
        index = self._handle_index(index)
        
        raw_xobject = pdfium.FPDF_NewXObjectFromPage(dest_pdf.raw, self.raw, index)
        if raw_xobject is None:
            raise PdfiumError("Failed to capture page %s as FPDF_XOBJECT" % index)
        
        return PdfXObject(
            raw = raw_xobject,
            pdf = dest_pdf,
        )
    
    
    def new_page(self, width, height, index=None):
        """
        Insert a new, empty page into the document.
        
        Parameters:
            width (float):
                Target page width (horizontal size).
            height (float):
                Target page height (vertical size).
            index (int | None):
                Suggested zero-based index at which the page will be inserted.
                If *index* is negative, the indexing direction will be reversed.
                If *index* is zero, the page will be inserted at the beginning.
                If *index* is :data:`None` or larger that the document's current last index, the page will be appended to the end.
        Returns:
            PdfPage: The newly created page.
        """
        if index is None:
            index = len(self)
        elif index < 0:
            index += len(self)
        raw_page = pdfium.FPDFPage_New(self.raw, index, width, height)
        return PdfPage(raw_page, self)
    
    
    def del_page(self, index):
        """
        Remove the page at *index*. Reverse indexing is allowed.
        """
        index = self._handle_index(index)
        pdfium.FPDFPage_Delete(self.raw, index)
    
    
    def get_page(self, index):
        """
        Returns:
            PdfPage: The page at *index*. Reverse indexing is allowed.
        """
        index = self._handle_index(index)
        raw_page = pdfium.FPDF_LoadPage(self.raw, index)
        return PdfPage(raw_page, self)
    
    
    def add_font(self, font_path, type, is_cid):
        """
        Add a font to the document.
        
        Parameters:
            font_path (str):
                File path of the font to use.
            type (int):
                A constant signifying the type of the given font (:data:`.FPDF_FONT_*`).
            is_cid (bool):
                Whether the given font is a CID font or not.
        Returns:
            PdfFont: A PDF font helper object.
        """
        
        with open(font_path, "rb") as fh:
            font_data = fh.read()
        
        pdf_font = pdfium.FPDFText_LoadFont(
            self.raw,
            ctypes.cast(font_data, ctypes.POINTER(ctypes.c_uint8)),
            len(font_data),
            type,
            is_cid,
        )
        
        return PdfFont(pdf_font, self, font_data)
    
    
    def _get_bookmark(self, bookmark, level):
        
        n_bytes = pdfium.FPDFBookmark_GetTitle(bookmark, None, 0)
        buffer = ctypes.create_string_buffer(n_bytes)
        pdfium.FPDFBookmark_GetTitle(bookmark, buffer, n_bytes)
        title = buffer.raw[:n_bytes-2].decode('utf-16-le')
        
        count = pdfium.FPDFBookmark_GetCount(bookmark)
        if count < 0:
            is_closed = True
        elif count == 0:
            is_closed = None
        else:
            is_closed = False
        
        n_kids = abs(count)
        dest = pdfium.FPDFBookmark_GetDest(self.raw, bookmark)
        page_index = pdfium.FPDFDest_GetDestPageIndex(self.raw, dest)
        if page_index == -1:
            page_index = None
        
        n_params = ctypes.c_ulong()
        view_pos = (pdfium.FS_FLOAT * 4)()
        view_mode = pdfium.FPDFDest_GetView(dest, n_params, view_pos)
        view_pos = list(view_pos)[:n_params.value]
        
        return OutlineItem(
            level = level,
            title = title,
            is_closed = is_closed,
            n_kids = n_kids,
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
        
        if seen is None:
            seen = set()
        
        bookmark = pdfium.FPDFBookmark_GetFirstChild(self.raw, parent)
        
        while bookmark:
            
            address = ctypes.addressof(bookmark.contents)
            if address in seen:
                logger.warning("A circular bookmark reference was detected whilst parsing the table of contents.")
                break
            else:
                seen.add(address)
            
            yield self._get_bookmark(bookmark, level)
            if level < max_depth-1:
                yield from self.get_toc(
                    max_depth = max_depth,
                    parent = bookmark,
                    level = level + 1,
                    seen = seen,
                )
            
            bookmark = pdfium.FPDFBookmark_GetNextSibling(self.raw, bookmark)
    
    
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
            
            if item.n_kids == 0:
                state = "*"
            elif item.is_closed:
                state = "-"
            else:
                state = "+"
            
            if item.page_index is None:
                target = "?"
            else:
                target = item.page_index + 1
            
            print(
                "    " * item.level +
                "[%s] %s -> %s  # %s %s" % (
                    state, item.title, target,
                    ViewmodeToStr[item.view_mode],
                    [round(c, n_digits) for c in item.view_pos],
                )
            )
    
    
    def update_rendering_input(self):
        """
        Update the input sources for concurrent rendering to the document's current state
        by saving to bytes and setting the result as new input.
        If you modified the document, you may want to call this method before :meth:`.render_to`.
        """
        buffer = io.BytesIO()
        self.save(buffer)
        buffer.seek(0)
        self._rendering_input = buffer.read()
        buffer.close()
    
    
    @classmethod
    def _process_page(cls, index, converter, input_data, password, file_access, **kwargs):
        pdf = cls(
            input_data,
            password = password,
            file_access = file_access,
        )
        page = pdf.get_page(index)
        result = page.render_to(converter, **kwargs)
        return result, index
    
    
    def render_to(
            self,
            converter,
            page_indices = None,
            n_processes = os.cpu_count(),
            **kwargs
        ):
        """
        Concurrently render multiple pages, using a process pool executor.
        
        If rendering only a single page, the call is simply forwarded to :meth:`.PdfPage.render_to` as a shortcut.
        
        Parameters:
            page_indices (typing.Sequence[int] | None):
                A sequence of zero-based indices of the pages to render. Reverse indexing or duplicate page indices are prohibited.
                If :data:`None`, all pages will be included. The order of results is guaranteed to match the order of given page indices.
            n_processes (int):
                Target number of parallel processes.
            kwargs (dict):
                Keyword arguments to the renderer. See :meth:`.PdfPage.render_to` / :meth:`.PdfPage.render_base`.
        
        Yields:
            :data:`typing.Any`: Implementation-specific result object.
        """
        
        n_pages = len(self)
        if not page_indices:
            page_indices = [i for i in range(n_pages)]
        else:
            if not all(0 <= i < n_pages for i in page_indices):
                raise ValueError("Out-of-bounds page index")
            if len(page_indices) != len(set(page_indices)):
                raise ValueError("Duplicate page index")
        
        # shortcut: if we're rendering just a single page, don't waste time setting up a process pool
        if len(page_indices) == 1:
            page = self.get_page(page_indices[0])
            result = page.render_to(converter, **kwargs)
            yield result
            return
        
        if self._rendering_input is None:
            if isinstance(self._orig_input, pdfium.FPDF_DOCUMENT):
                logger.warning("Cannot perform concurrent processing without input sources - saving the document implicitly to get picklable data.")
                self.update_rendering_input()
            elif is_input_buffer(self._orig_input):
                logger.warning("Cannot perform concurrent rendering with buffer input - reading the whole buffer into memory implicitly.")
                cursor = self._orig_input.tell()
                self._orig_input.seek(0)
                self._rendering_input = self._orig_input.read()
                self._orig_input.seek(cursor)
            else:
                self._rendering_input = self._orig_input
        
        invoke_renderer = functools.partial(
            PdfDocument._process_page,
            converter = converter,
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


def _open_pdf(input_data, password=None):
    
    if isinstance(password, str):
        password = password.encode("utf-8")
    
    ld_data = ()
    if isinstance(input_data, str):
        pdf = pdfium.FPDF_LoadDocument(input_data.encode("utf-8"), password)
    elif isinstance(input_data, bytes):
        pdf = pdfium.FPDF_LoadMemDocument64(input_data, len(input_data), password)
        ld_data = (input_data, )
    elif is_input_buffer(input_data):
        fileaccess, ld_data = get_fileaccess(input_data)
        pdf = pdfium.FPDF_LoadCustomDocument(fileaccess, password)
    else:
        raise TypeError("Invalid input type '%s'" % type(input_data).__name__)
    
    if pdfium.FPDF_GetPageCount(pdf) < 1:
        err_code = pdfium.FPDF_GetLastError()
        pdfium_msg = ErrorToStr.get(err_code, "Error code %s" % err_code)
        raise PdfiumError("Loading the document failed (PDFium: %s)" % pdfium_msg)
    
    return pdf, ld_data


class _writer_class:
    
    def __init__(self, buffer):
        self.buffer = buffer
        if not callable( getattr(self.buffer, "write", None) ):
            raise ValueError("Output buffer must implement the write() method.")
    
    def __call__(self, _, data, size):
        block = ctypes.cast(data, ctypes.POINTER(ctypes.c_ubyte * size))
        self.buffer.write(block.contents)
        return 1


class PdfXObject:
    """
    XObject helper class.
    
    Attributes:
        raw (FPDF_XOBJECT): The underlying PDFium XObject handle.
        pdf (PdfDocument): Reference to the document this XObject belongs to.
    """
    
    def __init__(self, raw, pdf):
        self.raw = raw
        self.pdf = pdf
        self._finalizer = weakref.finalize(
            self, self._static_close,
            self.raw, self.pdf,
        )
    
    def _tree_closed(self):
        if self.raw is None:
            return True
        return self.pdf._tree_closed()
    
    @staticmethod
    def _static_close(raw, parent):
        # logger.debug("Closing XObject")
        if parent._tree_closed():
            logger.critical("Document closed before XObject (this is illegal). Document: %s" % parent)
        pdfium.FPDF_CloseXObject(raw)
    
    def close(self):
        """
        Free memory by applying the finalizer for the underlying PDFium XObject.
        Please refer to the generic note on ``close()`` methods for details.
        """
        if self.raw is None:
            logger.warning("Duplicate close call suppressed on XObject %s" % self)
            return
        self._finalizer()
        self.raw = None
    
    def as_pageobject(self):
        """
        Returns:
            PdfPageObject: A new pageobject referencing the XObject.
        """
        raw_pageobj = pdfium.FPDF_NewFormObjectFromXObject(self.raw)
        return PdfPageObject(
            raw = raw_pageobj,
            type = pdfium.FPDF_PAGEOBJ_FORM,
            pdf = self.pdf,
        )


class HarfbuzzFont:
    """ Harfbuzz font data helper class. """
    
    def __init__(self, font_path):
        if harfbuzz is None:
            raise RuntimeError("Font helpers require uharfbuzz to be installed.")
        self.blob = harfbuzz.Blob.from_file_path(font_path)
        self.face = harfbuzz.Face(self.blob)
        self.font = harfbuzz.Font(self.face)
        self.scale = self.font.scale[0]


class PdfFont:
    """
    PDF font data helper class.
    
    Attributes:
        raw (FPDF_FONT): The underlying PDFium font handle.
        pdf (PdfDocument): Reference to the document this font belongs to.
    """
    
    def __init__(self, raw, pdf, font_data):
        self.raw = raw
        self.pdf = pdf
        self._font_data = font_data
        self._finalizer = weakref.finalize(
            self, self._static_close,
            self.raw, self.pdf, self._font_data,
        )
    
    def _tree_closed(self):
        if self.raw is None:
            return True
        return self.pdf._tree_closed()
    
    @staticmethod
    def _static_close(raw, parent, font_data):
        # logger.debug("Closing font")
        if parent._tree_closed():
            logger.critical("Document closed before font (this is illegal). Document: %s" % parent)
        pdfium.FPDFFont_Close(raw)
        id(font_data)
    
    def close(self):
        """
        Free memory by applying the finalizer for the underlying PDFium font.
        Please refer to the generic note on ``close()`` methods for details.
        """
        if self.raw is None:
            logger.warning("Duplicate close call suppressed on font %s" % self)
            return
        self._finalizer()
        self.raw = None
