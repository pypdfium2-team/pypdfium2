# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import weakref
import ctypes
import logging
import functools
import threading
from pathlib import Path
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.misc import (
    OutlineItem,
    FileAccess,
    PdfiumError,
    ErrorToStr,
    ViewmodeToStr,
    get_functype,
    get_bufaccess,
    is_input_buffer,
)
from pypdfium2._helpers.page import PdfPage
from pypdfium2._helpers.bitmap import PdfBitmap
from pypdfium2._helpers.pageobjects import PdfObject

logger = logging.getLogger(__name__)


class PdfDocument:
    """
    Document helper class.
    
    Parameters:
        input_data (str | pathlib.Path | bytes | typing.BinaryIO | FPDF_DOCUMENT):
            The input PDF given as file path, bytes, byte buffer, or raw PDFium document handle.
            :func:`.is_input_buffer` defines which objects are recognised as byte buffers.
        password (str | bytes):
            A password to unlock the PDF, if encrypted.
            If the document is not encrypted but a password was given, PDFium should ignore it.
        file_access (FileAccess):
            The file access strategy to use, if the input is a file path.
        autoclose (bool):
            Whether byte buffer input should be automatically closed on finalization.
    
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
        self._actual_input = self._orig_input
        self._password = password
        self._file_access = file_access
        self._autoclose = autoclose
        
        self._data_holder = []
        self._data_closer = []
        self._form_env = None
        self._form_config = None
        self._form_finalizer = None
        
        if isinstance(self._orig_input, str):
            self._orig_input = Path(self._orig_input)
        
        if isinstance(self._orig_input, Path):
            
            self._orig_input = self._orig_input.expanduser().resolve()
            if not self._orig_input.exists():
                raise FileNotFoundError("File does not exist: '%s'" % self._orig_input)
            
            if self._file_access is FileAccess.NATIVE:
                self._actual_input = self._orig_input
            elif self._file_access is FileAccess.BUFFER:
                self._actual_input = open(self._orig_input, "rb")
                self._data_closer.append(self._actual_input)
            elif self._file_access is FileAccess.BYTES:
                buf = open(self._orig_input, "rb")
                self._actual_input = buf.read()
                buf.close()
            else:
                raise ValueError("Invalid or unhandled file access strategy given.")
        
        if isinstance(self._actual_input, pdfium.FPDF_DOCUMENT):
            self.raw = self._actual_input
        else:
            self.raw, to_hold, to_close = _open_pdf(self._actual_input, self._password, self._autoclose)
            self._data_holder += to_hold
            self._data_closer += to_close
        
        self._finalizer = weakref.finalize(
            self, self._static_close,
            self.raw, self._data_holder, self._data_closer,
        )
    
    
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
    
    
    def _tree_closed(self):
        return (self.raw is None)
    
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
        # TODO
        """
        if self._form_env is None:
            return
        self._form_finalizer()
        self._form_env = None
        self._form_config = None
    
    
    def get_formtype(self):
        """
        # TODO
        """
        return pdfium.FPDF_GetFormType(self.raw)
    
    
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
        filewrite.WriteBlock = get_functype(pdfium.FPDF_FILEWRITE, "WriteBlock")( _buffer_writer(buffer) )
        
        saveargs = (self.raw, filewrite, pdfium.FPDF_NO_INCREMENTAL)
        if version is None:
            success = pdfium.FPDF_SaveAsCopy(*saveargs)
        else:
            success = pdfium.FPDF_SaveWithVersion(*saveargs, version)
        
        if not success:
            raise PdfiumError("Saving the document failed")
    
    
    def get_version(self):
        """
        Returns:
            int | None: The PDF version of the document (14 for 1.4, 15 for 1.5, ...),
            or :data:`None` if the document is new or its version could not be determined.
        """
        version = ctypes.c_int()
        success = pdfium.FPDF_GetFileVersion(self.raw, version)
        if not success:
            return None
        return version.value
    
    
    def get_page(self, index):
        """
        Returns:
            PdfPage: The page at *index*.
        """
        raw_page = pdfium.FPDF_LoadPage(self.raw, index)
        return PdfPage(raw_page, self)
    
    
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
                If :data:`None` or larger that the document's current last index, the page will be appended to the end.
        Returns:
            PdfPage: The newly created page.
        """
        if index is None:
            index = len(self)
        raw_page = pdfium.FPDFPage_New(self.raw, index, width, height)
        return PdfPage(raw_page, self)
    
    
    def del_page(self, index):
        """
        Remove the page at *index*.
        """
        pdfium.FPDFPage_Delete(self.raw, index)
    
    
    def import_pages(self, pdf, pages=None, index=None):
        """
        Import pages from a foreign document.
        
        Parameters:
            pdf (PdfDocument):
                The document from which to import pages.
            pages (typing.Sequence[int] | str | None):
                The pages to include. It may either be a list of zero-based page indices, or a string of one-based page numbers and ranges.
                If :data:`None`, all pages will be included.
            index (int):
                Zero-based index at which to insert the given pages. If :data:`None`, the pages are appended to the end of the document.
        """
        # TODO testing
        
        if index is None:
            index = len(self)
        
        if isinstance(pages, str):
            success = pdfium.FPDF_ImportPages(self.raw, pdf.raw, pages, index)
        else:
            page_count = 0
            c_pages = None
            if pages:
                page_count = len(pages)
                c_pages = (ctypes.c_int * page_count)(*pages)
            success = pdfium.FPDF_ImportPagesByIndex(self.raw, pdf.raw, c_pages, page_count, index)
        
        if not success:
            raise PdfiumError("Failed to import pages.")
    
    
    def get_page_size(self, index):
        """
        Get the dimensions of the page at *index*.
        
        Returns:
            (float, float): Page width and height in PDF canvas units.
        """
        size = pdfium.FS_SIZEF()
        success = pdfium.FPDF_GetPageSizeByIndexF(self.raw, index, size)
        if not success:
            raise PdfiumError("Getting page size by index failed.")
        return (size.width, size.height)
    
    
    def page_as_xobject(self, index, dest_pdf):
        """
        Capture a page as XObject and attach it to a document's resources.
        
        Parameters:
            index (int):
                Zero-based index of the page.
            dest_pdf (PdfDocument):
                Target document to which the XObject shall be added.
        Returns:
            PdfXObject: The page as XObject.
        """
        
        raw_xobject = pdfium.FPDF_NewXObjectFromPage(dest_pdf.raw, self.raw, index)
        if raw_xobject is None:
            raise PdfiumError("Failed to capture page %s as FPDF_XOBJECT" % index)
        
        return PdfXObject(
            raw = raw_xobject,
            pdf = dest_pdf,
        )
    
    
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
        Iterate through the bookmarks in the document's table of contents.
        
        Parameters:
            max_depth (int):
                Maximum recursion depth to consider.
        Yields:
            :class:`.OutlineItem`: Bookmark information.
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
    
    
    @classmethod
    def _process_page(cls, index, input_data, password, file_access, converter, renderer, **kwargs):
        pdf = cls(
            input_data,
            password = password,
            file_access = file_access,
        )
        page = pdf.get_page(index)
        return renderer(page, converter, **kwargs)
    
    
    @staticmethod
    def _handle_requests(requests, results):
        while True:
            request = requests.get()
            if request is None:  # stop
                break
            results.put(request)
    
    
    def render(
            self,
            converter,
            page_indices = None,
            n_processes = os.cpu_count(),
            renderer = PdfPage.render,
            **kwargs
        ):
        """
        Render multiple pages in parallel, using a process pool executor.
        
        Parameters:
            converter (typing.Callable):
                A function to convert the rendering output. See :class:`.PdfBitmap` for built-in converters.
            page_indices (typing.Sequence[int] | None):
                A sequence of zero-based indices of the pages to render. Duplicate page indices are prohibited.
                If :data:`None`, all pages will be included. The order of results matches the order of given page indices.
                (If rendering only a single page, the call is forwarded to the renderer directly.)
            n_processes (int):
                The number of parallel process to use.
            renderer (typing.Callable):
                The page rendering function to use. This may be used to plug in custom renderers other than :meth:`.PdfPage.render`.
            kwargs (dict):
                Keyword arguments to the renderer.
        
        Yields:
            :data:`typing.Any`: Converter-specific result object.
        """
        
        if isinstance(self._orig_input, pdfium.FPDF_DOCUMENT):
            raise ValueError("Cannot render in parallel without input sources.")
        elif is_input_buffer(self._orig_input):
            raise ValueError("Cannot render in parallel with buffer input.")
        
        n_pages = len(self)
        if not page_indices:
            page_indices = [i for i in range(n_pages)]
        else:
            if not all(0 <= i < n_pages for i in page_indices):
                raise ValueError("Out-of-bounds page index")
            if len(page_indices) != len(set(page_indices)):
                raise ValueError("Duplicate page index")
        
        manager = mp.Manager()
        requests = manager.Queue()
        results = manager.Queue()
        bitmap_maker = _shared_bitmap_maker(requests, results)
        
        invoke_renderer = functools.partial(
            PdfDocument._process_page,
            input_data = self._orig_input,
            password = self._password,
            file_access = self._file_access,
            converter = converter,
            renderer = renderer,
            bitmap_maker = bitmap_maker,
            **kwargs
        )
        
        request_handler = threading.Thread(
            target = self._handle_requests,
            args = (requests, results),
        )
        request_handler.start()
        
        with ProcessPoolExecutor(n_processes) as pool:
            yield from pool.map(invoke_renderer, page_indices)
        
        requests.put(None)  # stop
        request_handler.join()


class _shared_bitmap_maker:
    
    def __init__(self, requests, results):
        self.requests = requests
        self.results = results
    
    def __call__(self, width, height, format, rev_byteorder):
        request = (width, height, format, rev_byteorder)
        self.requests.put(request)
        answer = self.results.get()
        assert answer == request
        return PdfBitmap.new_native(width, height, format, rev_byteorder)


def _open_pdf(input_data, password, autoclose):
    
    if isinstance(password, str):
        password = password.encode("utf-8")
    
    to_hold = ()
    to_close = ()
    
    if isinstance(input_data, Path):
        pdf = pdfium.FPDF_LoadDocument(str(input_data).encode("utf-8"), password)
    elif isinstance(input_data, bytes):
        pdf = pdfium.FPDF_LoadMemDocument64(input_data, len(input_data), password)
        to_hold = (input_data, )
    elif is_input_buffer(input_data):
        bufaccess, to_hold = get_bufaccess(input_data)
        if autoclose:
            to_close = (input_data, )
        pdf = pdfium.FPDF_LoadCustomDocument(bufaccess, password)
    else:
        raise TypeError("Invalid input type '%s'" % type(input_data).__name__)
    
    if pdfium.FPDF_GetPageCount(pdf) < 1:
        err_code = pdfium.FPDF_GetLastError()
        pdfium_msg = ErrorToStr.get(err_code, "Error code %s" % err_code)
        raise PdfiumError("Loading the document failed (PDFium: %s)" % pdfium_msg)
    
    return pdf, to_hold, to_close


class _buffer_writer:
    
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
    
    
    def as_pageobject(self):
        """
        Returns:
            PdfObject: An independent page object representation of the XObject.
            If multiple page objects are created from one XObject, they share resources.
            Page objects created from an XObject remain valid after the XObject is finalized.
        """
        raw_pageobj = pdfium.FPDF_NewFormObjectFromXObject(self.raw)
        return PdfObject(
            raw = raw_pageobj,
            pdf = self.pdf,
        )
