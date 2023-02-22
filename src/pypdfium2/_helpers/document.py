# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ["PdfDocument", "PdfFormEnv", "PdfXObject", "PdfOutlineItem"]

import os
import ctypes
import logging
import functools
from pathlib import Path
from collections import namedtuple
from concurrent.futures import ProcessPoolExecutor

import pypdfium2.raw as pdfium_c
from pypdfium2._helpers.misc import PdfiumError
from pypdfium2._helpers.page import PdfPage
from pypdfium2._helpers.pageobjects import PdfObject
from pypdfium2._helpers.attachment import PdfAttachment
from pypdfium2._helpers._internal import consts, utils
from pypdfium2._helpers._internal.bases import AutoCloseable

logger = logging.getLogger(__name__)


class PdfDocument (AutoCloseable):
    """
    Document helper class.
    
    Parameters:
        input_data (str | pathlib.Path | bytes | ctypes.Array | typing.BinaryIO | FPDF_DOCUMENT):
            The input PDF given as file path, bytes, ctypes array, byte buffer, or raw PDFium document handle.
            A byte buffer is defined as an object that implements ``seek() tell() read() readinto()``.
        password (str | None):
            A password to unlock the PDF, if encrypted. Otherwise, None or an empty string may be passed.
            If a password is given but the PDF is not encrypted, it will be ignored (as of PDFium 5418).
        autoclose (bool):
            Whether byte buffer input should be automatically closed on finalization.
        may_init_forms (bool):
            Whether a form env may be initialized, if the document has forms.
    
    Raises:
        PdfiumError: Raised if the document failed to load. The exception message is annotated with the reason reported by PDFium.
        FileNotFoundError: Raised if an invalid or non-existent file path was given.
    
    Hint:
        * :func:`len` may be called to get a document's number of pages.
        * Looping over a document will yield its pages from beginning to end.
        * Pages may be loaded using list index access.
        * The ``del`` keyword and list index access may be used to delete pages.
    
    Attributes:
        raw (FPDF_DOCUMENT):
            The underlying PDFium document handle.
        formenv (PdfFormEnv | None):
            Form env, if the document has forms and ``may_init_forms=True``.
        formtype (int):
            PDFium form type that applies to the document (:attr:`FORMTYPE_*`).
            ``FORMTYPE_NONE`` if the document has no forms or ``may_init_forms=False``.
    """
    
    def __init__(
            self,
            input,
            password = None,
            autoclose = False,
            may_init_forms = True,
        ):
        
        if isinstance(input, str):
            input = Path(input)
        if isinstance(input, Path):
            input = input.expanduser().resolve()
            if not input.is_file():
                raise FileNotFoundError(input)
        
        self._input = input
        self._password = password
        self._autoclose = autoclose
        
        self._data_holder = []
        self._data_closer = []
        
        if isinstance(self._input, pdfium_c.FPDF_DOCUMENT):
            self.raw = self._input
        else:
            self.raw, to_hold, to_close = _open_pdf(self._input, self._password, self._autoclose)
            self._data_holder += to_hold
            self._data_closer += to_close
        
        AutoCloseable.__init__(self, self._close_impl, self._data_holder, self._data_closer)
        
        self.formenv = None
        if may_init_forms:
            self.formtype = pdfium_c.FPDF_GetFormType(self)
            self._has_forms = self.formtype != pdfium_c.FORMTYPE_NONE  # TODO maybe make public?
            if self._has_forms:
                formconfig = pdfium_c.FPDF_FORMFILLINFO(version=2)
                raw = pdfium_c.FPDFDOC_InitFormFillEnvironment(self, formconfig)
                self.formenv = PdfFormEnv(raw, formconfig, self)
        else:
            self.formtype = pdfium_c.FORMTYPE_NONE
            self._has_forms = False
    
    
    @property
    def parent(self):  # AutoCloseable hook
        return None
    
    
    @staticmethod
    def _close_impl(raw, data_holder, data_closer):
        # can't close formenv here, would cause circular reference
        pdfium_c.FPDF_CloseDocument(raw)
        for data in data_holder:
            id(data)
        for data in data_closer:
            data.close()
        data_holder.clear()
        data_closer.clear()
    
    
    def close(self):
        if self.formenv:
            self.formenv.close()
        AutoCloseable.close(self)
    
    
    def __len__(self):
        return pdfium_c.FPDF_GetPageCount(self)
    
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
    
    
    def get_pagemode(self):
        """
        Returns:
            int: Page displaying mode (:attr:`PAGEMODE_*`).
        """
        return pdfium_c.FPDFDoc_GetPageMode(self)
    
    
    def is_tagged(self):
        """
        Returns:
            bool: Whether the document is tagged (cf. PDF 1.7, 10.7 "Tagged PDF").
        """
        return bool( pdfium_c.FPDFCatalog_IsTagged(self) )
    
    
    def _save_to(self, buffer, version=None, flags=pdfium_c.FPDF_NO_INCREMENTAL):
        
        c_writer = utils.get_bufwriter(buffer)
        saveargs = (self, c_writer, flags)
        
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
        n_bytes = pdfium_c.FPDF_GetFileIdentifier(self, type, None, 0)
        buffer = ctypes.create_string_buffer(n_bytes)
        pdfium_c.FPDF_GetFileIdentifier(self, type, buffer, n_bytes)
        return buffer.raw[:n_bytes-2]
    
    
    def get_version(self):
        """
        Returns:
            int | None: The PDF version of the document (14 for 1.4, 15 for 1.5, ...),
            or None if the document is new or its version could not be determined.
        """
        version = ctypes.c_int()
        success = pdfium_c.FPDF_GetFileVersion(self, version)
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
        n_bytes = pdfium_c.FPDF_GetMetaText(self, enc_key, None, 0)
        buffer = ctypes.create_string_buffer(n_bytes)
        pdfium_c.FPDF_GetMetaText(self, enc_key, buffer, n_bytes)
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
        return pdfium_c.FPDFDoc_GetAttachmentCount(self)
    
    
    def get_attachment(self, index):
        """
        Returns:
            PdfAttachment: The attachment at *index* (zero-based).
        """
        raw_attachment = pdfium_c.FPDFDoc_GetAttachment(self, index)
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
        raw_attachment = pdfium_c.FPDFDoc_AddAttachment(self, enc_name_ptr)
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
        success = pdfium_c.FPDFDoc_DeleteAttachment(self, index)
        if not success:
            raise PdfiumError("Failed to delete attachment at index %s." % (index, ))
    
    
    def get_page(self, index):
        """
        Returns:
            PdfPage: The page at *index* (zero-based).
        Note:
            This calls ``FORM_OnAfterLoadPage()`` if the document has an active form env.
            The form env must no be closed before the page is closed!
        """
        
        raw_page = pdfium_c.FPDF_LoadPage(self, index)
        if not raw_page:
            raise PdfiumError("Failed to load page.")
        page = PdfPage(raw_page, self)
        
        if self.formenv:
            pdfium_c.FORM_OnAfterLoadPage(page, self.formenv)
        # TODO attach page to formenv and add safety check on form env closing
        
        return page
    
    
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
        raw_page = pdfium_c.FPDFPage_New(self, index, width, height)
        return PdfPage(raw_page, self)
    
    
    def del_page(self, index):
        """
        Remove the page at *index* (zero-based).
        """
        pdfium_c.FPDFPage_Delete(self, index)
    
    
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
            success = pdfium_c.FPDF_ImportPages(self, pdf, pages.encode("ascii"), index)
        else:
            page_count = 0
            c_pages = None
            if pages:
                page_count = len(pages)
                c_pages = (ctypes.c_int * page_count)(*pages)
            success = pdfium_c.FPDF_ImportPagesByIndex(self, pdf, c_pages, page_count, index)
        
        if not success:
            raise PdfiumError("Failed to import pages.")
    
    
    def get_page_size(self, index):
        """
        Returns:
            (float, float): Width and height in PDF canvas units of the page at *index* (zero-based).
        """
        size = pdfium_c.FS_SIZEF()
        success = pdfium_c.FPDF_GetPageSizeByIndexF(self, index, size)
        if not success:
            raise PdfiumError("Failed to get page size by index.")
        return (size.width, size.height)
    
    
    def get_page_label(self, index):
        """
        Returns:
            str: Label of the page at *index* (zero-based).
            (A page label is essentially an alias that may be displayed instead of the page number.)
        """
        n_bytes = pdfium_c.FPDF_GetPageLabel(self, index, None, 0)
        buffer = ctypes.create_string_buffer(n_bytes)
        pdfium_c.FPDF_GetPageLabel(self, index, buffer, n_bytes)
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
        
        raw_xobject = pdfium_c.FPDF_NewXObjectFromPage(dest_pdf, self, index)
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
        dest = pdfium_c.FPDFBookmark_GetDest(self, bookmark)
        page_index = pdfium_c.FPDFDest_GetDestPageIndex(self, dest)
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
        
        bookmark = pdfium_c.FPDFBookmark_GetFirstChild(self, parent)
        
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
            
            bookmark = pdfium_c.FPDFBookmark_GetNextSibling(self, bookmark)
    
    
    @classmethod
    def _process_page(cls, index, input_data, password, renderer, converter, pass_info, **kwargs):
        
        pdf = cls(
            input_data,
            password = password,
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
            If your code shall be frozen into an executable, :func:`multiprocessing.freeze_support`
            needs to be called at the start of the ``if __name__ == "__main__":`` block if using this method.
        
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
        
        if not isinstance(self._input, (Path, str)):
            raise ValueError("Can only render in parallel with file path input.")
        
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
            input_data = self._input,
            password = self._password,
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
            Accompanying form configuration interface, to be kept alive.
        pdf (PdfDocument):
            Parent document this form env belongs to.
    """
    
    def __init__(self, raw, config, pdf):
        self.raw = raw
        self.config = config
        self.pdf = pdf
        AutoCloseable.__init__(self, self._close_impl, self.config, self.pdf)
    
    @property
    def parent(self):  # AutoCloseable hook
        return self.pdf
    
    @staticmethod
    def _close_impl(raw, config, pdf):
        pdfium_c.FPDFDOC_ExitFormFillEnvironment(raw)
        id(config)
        pdf.formenv = None


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
    def parent(self):  # AutoCloseable hook
        return self.pdf
    
    def as_pageobject(self):
        """
        Returns:
            PdfObject: An independent page object representation of the XObject.
            If multiple page objects are created from one XObject, they share resources.
            Page objects created from an XObject remain valid after the XObject is closed.
        """
        raw_pageobj = pdfium_c.FPDF_NewFormObjectFromXObject(self)
        return PdfObject(
            raw = raw_pageobj,
            pdf = self.pdf,
        )


def _open_pdf(input_data, password, autoclose):
    
    to_hold = ()
    to_close = ()
    
    if password is not None:
        password = (password + "\x00").encode("utf-8")
    
    if isinstance(input_data, Path):
        pdf = pdfium_c.FPDF_LoadDocument((str(input_data) + "\x00").encode("utf-8"), password)
    elif isinstance(input_data, (bytes, ctypes.Array)):
        pdf = pdfium_c.FPDF_LoadMemDocument64(input_data, len(input_data), password)
        to_hold = (input_data, )
    elif utils.is_buffer(input_data, "r"):
        bufaccess, to_hold = utils.get_bufreader(input_data)
        if autoclose:
            to_close = (input_data, )
        pdf = pdfium_c.FPDF_LoadCustomDocument(bufaccess, password)
    else:
        raise TypeError("Invalid input type '%s'" % type(input_data).__name__)
    
    if pdfium_c.FPDF_GetPageCount(pdf) < 1:
        err_code = pdfium_c.FPDF_GetLastError()
        raise PdfiumError("Failed to load document (PDFium: %s)." % consts.ErrorToStr.get(err_code))
    
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
