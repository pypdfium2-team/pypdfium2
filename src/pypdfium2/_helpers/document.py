# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ["PdfDocument", "PdfFormEnv", "PdfXObject", "PdfOutlineItem"]

import os
import os.path
import ctypes
import logging
import functools
from pathlib import Path
from collections import namedtuple
from concurrent.futures import ProcessPoolExecutor

import pypdfium2.raw as pdfium_c
from pypdfium2._helpers.misc import (
    FileAccessMode,
    PdfiumError,
)
from pypdfium2._helpers.page import PdfPage
from pypdfium2._helpers.pageobjects import PdfObject
from pypdfium2._helpers.attachment import PdfAttachment
from pypdfium2._helpers._internal import consts, utils
from pypdfium2._helpers._internal.autoclose import AutoCloseable

logger = logging.getLogger(__name__)


class PdfDocument (AutoCloseable):
    """
    Document helper class.
    
    Parameters:
        input_data (str | pathlib.Path | bytes | ctypes.Array | typing.BinaryIO | FPDF_DOCUMENT):
            The input PDF given as file path, bytes, ctypes array, byte buffer, or raw PDFium document handle.
            A byte buffer is defined as an object that implements ``seek()``, ``tell()``, ``read()`` and ``readinto()``.
        password (str | None):
            A password to unlock the PDF, if encrypted. Otherwise, None or an empty string may be passed.
            If a password is given but the PDF is not encrypted, it will be ignored (as of PDFium 5418).
        file_access (FileAccessMode):
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
            file_access = FileAccessMode.NATIVE,
            autoclose = False,
        ):
        
        # TODO rename orig_input to something better
        self._orig_input = input_data
        self._actual_input = self._orig_input
        self._password = password
        self._file_access = file_access
        self._autoclose = autoclose
        
        self._data_holder = []
        self._data_closer = []
        self._formenv = None
        
        if isinstance(self._orig_input, Path):
            self._orig_input = str(self._orig_input)
        
        if isinstance(self._orig_input, str):
            
            self._orig_input = os.path.abspath(os.path.expanduser(self._orig_input))
            if not os.path.exists(self._orig_input):
                raise FileNotFoundError(self._orig_input)
            
            if self._file_access is FileAccessMode.NATIVE:
                self._actual_input = self._orig_input
            elif self._file_access is FileAccessMode.BUFFER:
                self._actual_input = open(self._orig_input, "rb")
                self._autoclose = True
            elif self._file_access is FileAccessMode.BYTES:
                with open(self._orig_input, "rb") as buf:
                    self._actual_input = buf.read()
            else:
                raise ValueError("Invalid or unhandled file access strategy given.")
        
        if isinstance(self._actual_input, pdfium_c.FPDF_DOCUMENT):
            self.raw = self._actual_input
        else:
            self.raw, to_hold, to_close = _open_pdf(self._actual_input, self._password, self._autoclose)
            self._data_holder += to_hold
            self._data_closer += to_close
        
        AutoCloseable.__init__(self, self._close_impl, self._data_holder, self._data_closer)
    
    
    @staticmethod
    def _close_impl(raw, data_holder, data_closer):
        pdfium_c.FPDF_CloseDocument(raw)
        for data in data_holder:
            id(data)
        for data in data_closer:
            data.close()
        data_holder.clear()
        data_closer.clear()
    
    
    def close(self):
        if self._formenv is not None:
            self._formenv.close()
        AutoCloseable.close(self)
    
    
    def __len__(self):
        return pdfium_c.FPDF_GetPageCount(self.raw)
    
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
        new_pdf = pdfium_c.FPDF_CreateNewDocument()
        return cls(new_pdf)
    
    
    def init_formenv(self, config=None):
        """
        Initialise a form environment for this document.
        If already initialised, the existing handle will be returned.
        
        Parameters:
            config (FPDF_FORMFILLINFO | None):
                Form configuration interface. If None, a default one will be used.
        Returns:
            PdfFormEnv: Handle to the form environment.
        """
        
        if self._formenv is not None:
            return self._formenv
        
        if config is None:
            config = pdfium_c.FPDF_FORMFILLINFO()
            config.version = 2
        
        raw = pdfium_c.FPDFDOC_InitFormFillEnvironment(self.raw, config)
        self._formenv = PdfFormEnv(raw, config, self)
        
        return self._formenv
    
    
    def get_formtype(self):
        """
        Returns:
            int: The form type of the document (:attr:`FORMTYPE_*`). :attr:`FORMTYPE_NONE` if it has no forms.
        """
        return pdfium_c.FPDF_GetFormType(self.raw)
    
    
    def get_pagemode(self):
        """
        Returns:
            int: Page displaying mode (:attr:`PAGEMODE_*`).
        """
        return pdfium_c.FPDFDoc_GetPageMode(self.raw)
    
    
    def _save_to(self, buffer, version=None, flags=pdfium_c.FPDF_NO_INCREMENTAL):
        
        c_writer = utils.get_bufwriter(buffer)
        saveargs = (self.raw, c_writer, flags)
        
        if version is None:
            success = pdfium_c.FPDF_SaveAsCopy(*saveargs)
        else:
            success = pdfium_c.FPDF_SaveWithVersion(*saveargs, version)
        
        if not success:
            raise PdfiumError("Failed to save document.")
    
    
    def save(self, dest, *args, **kwargs):
        """
        Save the document at its current state.
        
        Parameters:
            dest (str | pathlib.Path | io.BytesIO):
                File path or byte buffer the document shall be written to.
            version (int | None):
                The PDF version to use, given as an integer (14 for 1.4, 15 for 1.5, ...).
                If None (the default), PDFium will set a version automatically.
            flags (int):
                PDFium saving flags (defaults to :attr:`FPDF_NO_INCREMENTAL`).
        """
        if isinstance(dest, (str, Path)):
            with open(dest, "wb") as buf:
                self._save_to(buf, *args, **kwargs)
        elif utils.is_buffer(dest, "w"):
            self._save_to(dest, *args, **kwargs)
        else:
            raise ValueError("Cannot save to '%s'" % (dest, ))
    
        
    def get_identifier(self, type=pdfium_c.FILEIDTYPE_PERMANENT):
        """
        Parameters:
            type (int):
                The identifier type to retrieve (:attr:`FILEIDTYPE_*`), either permanent or changing.
                If the file was updated incrementally, the permanent identifier stays the same,
                while the changing identifier is re-calculated.
        Returns:
            bytes: Unique file identifier from the PDF's trailer dictionary.
            See PDF 1.7, Section 14.4 "File Identifiers".
        """
        n_bytes = pdfium_c.FPDF_GetFileIdentifier(self.raw, type, None, 0)
        buffer = ctypes.create_string_buffer(n_bytes)
        pdfium_c.FPDF_GetFileIdentifier(self.raw, type, buffer, n_bytes)
        return buffer.raw[:n_bytes-2]
    
    
    def get_version(self):
        """
        Returns:
            int | None: The PDF version of the document (14 for 1.4, 15 for 1.5, ...),
            or None if the document is new or its version could not be determined.
        """
        version = ctypes.c_int()
        success = pdfium_c.FPDF_GetFileVersion(self.raw, version)
        if not success:
            return None
        return version.value
    
    
    def get_metadata_value(self, key):
        """
        Returns:
            str: Value of the given key in the PDF's metadata dictionary.
            If the key is not contained, an empty string will be returned.
        """
        enc_key = (key + "\x00").encode("utf-8")
        n_bytes = pdfium_c.FPDF_GetMetaText(self.raw, enc_key, None, 0)
        buffer = ctypes.create_string_buffer(n_bytes)
        pdfium_c.FPDF_GetMetaText(self.raw, enc_key, buffer, n_bytes)
        return buffer.raw[:n_bytes-2].decode("utf-16-le")
    
    
    METADATA_KEYS = ("Title", "Author", "Subject", "Keywords", "Creator", "Producer", "CreationDate", "ModDate")
    
    def get_metadata_dict(self, skip_empty=False):
        """
        Get the document's metadata as dictionary.
        
        Parameters:
            skip_empty (bool):
                If True, skip items whose value is an empty string.
        Returns:
            dict: PDF metadata.
        """
        metadata = {}
        for key in self.METADATA_KEYS:
            value = self.get_metadata_value(key)
            if skip_empty and not value:
                continue
            metadata[key] = value
        return metadata
    
    
    def count_attachments(self):
        """
        Returns:
            int: The number of embedded files in the document.
        """
        return pdfium_c.FPDFDoc_GetAttachmentCount(self.raw)
    
    
    def get_attachment(self, index):
        """
        Returns:
            PdfAttachment: The attachment at *index* (zero-based).
        """
        raw_attachment = pdfium_c.FPDFDoc_GetAttachment(self.raw, index)
        if not raw_attachment:
            raise PdfiumError("Failed to get attachment at index %s." % (index, ))
        return PdfAttachment(raw_attachment, self)
    
    
    def new_attachment(self, name):
        """
        Add a new attachment to the document. It may appear at an arbitrary index (as of PDFium 5418).
        
        Parameters:
            name (str):
                The name the attachment shall have. Usually a file name with extension.
        Returns:
            PdfAttachment: Handle to the new, empty attachment.
        """
        enc_name = (name + "\x00").encode("utf-16-le")
        enc_name_ptr = ctypes.cast(enc_name, pdfium_c.FPDF_WIDESTRING)
        raw_attachment = pdfium_c.FPDFDoc_AddAttachment(self.raw, enc_name_ptr)
        if not raw_attachment:
            raise PdfiumError("Failed to create new attachment '%s'." % (name, ))
        return PdfAttachment(raw_attachment, self)
    
    
    def del_attachment(self, index):
        """
        Unlink the attachment at *index* (zero-based).
        It will be hidden from the viewer, but is still present in the file (as of PDFium 5418).
        Following attachments shift one slot to the left in the array representation used by PDFium's API.
        
        Handles to the attachment in question received from :meth:`.get_attachment`
        must not be accessed anymore after this method has been called.
        """
        success = pdfium_c.FPDFDoc_DeleteAttachment(self.raw, index)
        if not success:
            raise PdfiumError("Failed to delete attachment at index %s." % (index, ))
    
    
    def get_page(self, index):
        """
        Returns:
            PdfPage: The page at *index* (zero-based).
        """
        raw_page = pdfium_c.FPDF_LoadPage(self.raw, index)
        if not raw_page:
            raise PdfiumError("Failed to load page.")
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
                Suggested zero-based index at which the page shall be inserted.
                If None or larger that the document's current last index, the page will be appended to the end.
        Returns:
            PdfPage: The newly created page.
        """
        if index is None:
            index = len(self)
        raw_page = pdfium_c.FPDFPage_New(self.raw, index, width, height)
        return PdfPage(raw_page, self)
    
    
    def del_page(self, index):
        """
        Remove the page at *index* (zero-based).
        """
        pdfium_c.FPDFPage_Delete(self.raw, index)
    
    
    def import_pages(self, pdf, pages=None, index=None):
        """
        Import pages from a foreign document.
        
        Parameters:
            pdf (PdfDocument):
                The document from which to import pages.
            pages (list[int] | str | None):
                The pages to include. It may either be a list of zero-based page indices, or a string of one-based page numbers and ranges.
                If None, all pages will be included.
            index (int):
                Zero-based index at which to insert the given pages. If None, they are appended to the end of the document.
        """
        
        if index is None:
            index = len(self)
        
        if isinstance(pages, str):
            success = pdfium_c.FPDF_ImportPages(self.raw, pdf.raw, pages, index)
        else:
            page_count = 0
            c_pages = None
            if pages:
                page_count = len(pages)
                c_pages = (ctypes.c_int * page_count)(*pages)
            success = pdfium_c.FPDF_ImportPagesByIndex(self.raw, pdf.raw, c_pages, page_count, index)
        
        if not success:
            raise PdfiumError("Failed to import pages.")
    
    
    def get_page_size(self, index):
        """
        Returns:
            (float, float): Width and height in PDF canvas units of the page at *index* (zero-based).
        """
        size = pdfium_c.FS_SIZEF()
        success = pdfium_c.FPDF_GetPageSizeByIndexF(self.raw, index, size)
        if not success:
            raise PdfiumError("Failed to get page size by index.")
        return (size.width, size.height)
    
    
    def get_page_label(self, index):
        """
        Returns:
            str: Label of the page at *index* (zero-based).
            (A page label is essentially an alias that may be displayed instead of the page number.)
        """
        n_bytes = pdfium_c.FPDF_GetPageLabel(self.raw, index, None, 0)
        buffer = ctypes.create_string_buffer(n_bytes)
        pdfium_c.FPDF_GetPageLabel(self.raw, index, buffer, n_bytes)
        return buffer.raw[:n_bytes-2].decode("utf-16-le")
    
    
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
        
        raw_xobject = pdfium_c.FPDF_NewXObjectFromPage(dest_pdf.raw, self.raw, index)
        if raw_xobject is None:
            raise PdfiumError("Failed to capture page %s as FPDF_XOBJECT." % index)
        
        return PdfXObject(
            raw = raw_xobject,
            pdf = dest_pdf,
        )
    
    
    def _get_bookmark(self, bookmark, level):
        
        n_bytes = pdfium_c.FPDFBookmark_GetTitle(bookmark, None, 0)
        buffer = ctypes.create_string_buffer(n_bytes)
        pdfium_c.FPDFBookmark_GetTitle(bookmark, buffer, n_bytes)
        title = buffer.raw[:n_bytes-2].decode('utf-16-le')
        
        count = pdfium_c.FPDFBookmark_GetCount(bookmark)
        if count < 0:
            is_closed = True
        elif count == 0:
            is_closed = None
        else:
            is_closed = False
        
        n_kids = abs(count)
        dest = pdfium_c.FPDFBookmark_GetDest(self.raw, bookmark)
        page_index = pdfium_c.FPDFDest_GetDestPageIndex(self.raw, dest)
        if page_index == -1:
            page_index = None
        
        n_params = ctypes.c_ulong()
        view_pos = (pdfium_c.FS_FLOAT * 4)()
        view_mode = pdfium_c.FPDFDest_GetView(dest, n_params, view_pos)
        view_pos = list(view_pos)[:n_params.value]
        
        return PdfOutlineItem(
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
            :class:`.PdfOutlineItem`: Bookmark information.
        """
        
        if seen is None:
            seen = set()
        
        bookmark = pdfium_c.FPDFBookmark_GetFirstChild(self.raw, parent)
        
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
            
            bookmark = pdfium_c.FPDFBookmark_GetNextSibling(self.raw, bookmark)
    
    
    # TODO change or remove ?
    @staticmethod
    def print_toc(toc, n_digits=2):
        """
        Print a table of contents.
        
        Parameters:
            toc (typing.Iterator[PdfOutlineItem]):
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
                    consts.ViewmodeToStr[item.view_mode],
                    [round(c, n_digits) for c in item.view_pos],
                )
            )
    
    
    @classmethod
    def _process_page(cls, index, input_data, password, file_access, renderer, converter, pass_info, **kwargs):
        
        pdf = cls(
            input_data,
            password = password,
            file_access = file_access,
        )
        page = pdf.get_page(index)
        
        bitmap = renderer(page, **kwargs)
        info = bitmap.get_info()
        result = converter(bitmap)
        
        for g in (bitmap, page, pdf):
            g.close()
        
        if pass_info:
            return result, info
        else:
            return result
    
    
    def render(
            self,
            converter,
            renderer = PdfPage.render,
            page_indices = None,
            n_processes = os.cpu_count(),
            pass_info = False,
            **kwargs
        ):
        """
        Render multiple pages in parallel, using a process pool executor.
        
        Hint:
            If your code shall be packaged into a Windows executable, :func:`multiprocessing.freeze_support`
            needs to be called at the start of your ``if __name__ == "__main__":`` block if using this method.
        
        Parameters:
            converter (typing.Callable):
                A function to convert the rendering output. See :class:`.PdfBitmap` for built-in converters.
            page_indices (list[int] | None):
                A sequence of zero-based indices of the pages to render. Duplicate page indices are prohibited.
                If None, all pages will be included. The order of results is supposed to match the order of given page indices.
            n_processes (int):
                The number of parallel process to use.
            renderer (typing.Callable):
                The page rendering function to use. This may be used to plug in custom renderers other than :meth:`.PdfPage.render`.
            kwargs (dict):
                Keyword arguments to the renderer.
        
        Yields:
            :data:`typing.Any`: Parameter-dependent result.
        """
        
        # BUG(#164): Rendering in parallel with buffer or bytes file access mode results in segfaults
        if not isinstance(self._orig_input, (str, Path)) or self._file_access is not FileAccessMode.NATIVE:
            raise ValueError("Can only render in parallel with file path input and native access mode.")
        
        n_pages = len(self)
        if not page_indices:
            page_indices = [i for i in range(n_pages)]
        else:
            if not all(0 <= i < n_pages for i in page_indices):
                raise ValueError("Out-of-bounds page indices are prohibited.")
            if len(page_indices) != len(set(page_indices)):
                raise ValueError("Duplicate page indices are prohibited.")
        
        invoke_renderer = functools.partial(
            PdfDocument._process_page,
            input_data = self._orig_input,
            password = self._password,
            file_access = self._file_access,
            renderer = renderer,
            converter = converter,
            pass_info = pass_info,
            **kwargs
        )
        
        with ProcessPoolExecutor(n_processes) as pool:
            yield from pool.map(invoke_renderer, page_indices)


class PdfFormEnv (AutoCloseable):
    """
    Form environment helper class.
    
    Attributes:
        raw (FPDF_FORMHANDLE):
            The underlying PDFium form env handle.
        config (FPDF_FORMFILLINFO):
            Accompanying form configuration interface. Needs to remain alive while the form env is used.
        pdf (PdfDocument):
            Parent document this form env belongs to.
    """
    
    def __init__(self, raw, config, pdf):
        self.raw = raw
        self.config = config
        self.pdf = pdf
        AutoCloseable.__init__(self, self._close_impl, self.config, self.pdf)
    
    @property
    def parent(self):
        return self.pdf
    
    @staticmethod
    def _close_impl(raw, config, pdf):
        pdfium_c.FPDFDOC_ExitFormFillEnvironment(raw)
        id(config)
        pdf._formenv = None


class PdfXObject (AutoCloseable):
    """
    XObject helper class.
    
    Attributes:
        raw (FPDF_XOBJECT): The underlying PDFium XObject handle.
        pdf (PdfDocument): Reference to the document this XObject belongs to.
    """
    
    def __init__(self, raw, pdf):
        self.raw = raw
        self.pdf = pdf
        AutoCloseable.__init__(self, pdfium_c.FPDF_CloseXObject)
    
    @property
    def parent(self):
        return self.pdf
    
    def as_pageobject(self):
        """
        Returns:
            PdfObject: An independent page object representation of the XObject.
            If multiple page objects are created from one XObject, they share resources.
            Page objects created from an XObject remain valid after the XObject is closed.
        """
        raw_pageobj = pdfium_c.FPDF_NewFormObjectFromXObject(self.raw)
        return PdfObject(
            raw = raw_pageobj,
            pdf = self.pdf,
        )


def _open_pdf(input_data, password, autoclose):
    
    to_hold = ()
    to_close = ()
    
    if password is not None:
        password = (password + "\x00").encode("utf-8")
    
    if isinstance(input_data, str):
        pdf = pdfium_c.FPDF_LoadDocument((input_data + "\x00").encode("utf-8"), password)
    elif utils.is_buffer(input_data, "r"):
        bufaccess, to_hold = utils.get_bufreader(input_data)
        if autoclose:
            to_close = (input_data, )
        pdf = pdfium_c.FPDF_LoadCustomDocument(bufaccess, password)
    elif isinstance(input_data, bytes) or isinstance(input_data, ctypes.Array):
        pdf = pdfium_c.FPDF_LoadMemDocument64(input_data, len(input_data), password)
        to_hold = (input_data, )
    else:
        raise TypeError("Invalid input type '%s'" % type(input_data).__name__)
    
    if pdfium_c.FPDF_GetPageCount(pdf) < 1:
        err_code = pdfium_c.FPDF_GetLastError()
        pdfium_msg = consts.ErrorToStr.get(err_code, "Error code %s" % err_code)
        raise PdfiumError("Failed to load document (PDFium: %s)." % pdfium_msg)
    
    return pdf, to_hold, to_close


PdfOutlineItem = namedtuple("PdfOutlineItem", "level title is_closed n_kids page_index view_mode view_pos")
"""
Bookmark information.

Parameters:
    level (int):
        Number of parent items.
    title (str):
        Title string of the bookmark.
    is_closed (bool):
        True if child items shall be collapsed, False if they shall be expanded.
        None if the item has no descendants (i. e. ``n_kids == 0``).
    n_kids (int):
        Absolute number of child items, according to the PDF.
    page_index (int | None):
        Zero-based index of the page the bookmark points to.
        May be None if the bookmark has no target page (or it could not be determined).
    view_mode (int):
        A view mode constant (:data:`PDFDEST_VIEW_*`) defining how the coordinates of *view_pos* shall be interpreted.
    view_pos (list[float]):
        Target position on the page the viewport should jump to when the bookmark is clicked.
        It is a sequence of :class:`float` values in PDF canvas units.
        Depending on *view_mode*, it may contain between 0 and 4 coordinates.
"""
