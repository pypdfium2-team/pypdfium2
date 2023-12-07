# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PdfDocument", "PdfFormEnv", "PdfXObject", "PdfOutlineItem")

import os
import ctypes
import logging
import inspect
import warnings
from pathlib import Path
from collections import namedtuple
import multiprocessing as mp

import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i
from pypdfium2.version import PDFIUM_INFO
from pypdfium2._helpers.misc import PdfiumError
from pypdfium2._helpers.page import PdfPage
from pypdfium2._helpers.pageobjects import PdfObject
from pypdfium2._helpers.attachment import PdfAttachment

logger = logging.getLogger(__name__)


class PdfDocument (pdfium_i.AutoCloseable):
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
            Form env, if the document has forms and :meth:`.init_forms` was called.
    """
    
    def __init__(self, input, password=None, autoclose=False):
        
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
        
        # question: can we make attributes like formenv effectively immutable for the caller?
        self.formenv = None
        
        if isinstance(self._input, pdfium_c.FPDF_DOCUMENT):
            self.raw = self._input
        else:
            self.raw, to_hold, to_close = _open_pdf(self._input, self._password, self._autoclose)
            self._data_holder += to_hold
            self._data_closer += to_close
        
        super().__init__(PdfDocument._close_impl, self._data_holder, self._data_closer)
    
    
    def __repr__(self):
        if isinstance(self._input, Path):
            input_r = repr( str(self._input) )
        elif isinstance(self._input, bytes):
            input_r = f"<bytes object at {hex(id(self._input))}>"
        elif isinstance(self._input, pdfium_c.FPDF_DOCUMENT):
            input_r = f"<FPDF_DOCUMENT at {hex(id(self._input))}>"
        else:
            input_r = repr(self._input)
        return f"{super().__repr__()[:-1]} from {input_r}>"
    
    
    @property
    def parent(self):  # AutoCloseable hook
        return None
    
    
    @staticmethod
    def _close_impl(raw, data_holder, data_closer):
        pdfium_c.FPDF_CloseDocument(raw)
        for data in data_holder:
            id(data)
        for data in data_closer:
            data.close()
        data_holder.clear()
        data_closer.clear()
    
    
    def __len__(self):
        return pdfium_c.FPDF_GetPageCount(self)
    
    def __iter__(self):
        for i in range( len(self) ):
            yield self[i]
    
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
    
    
    def init_forms(self, config=None):
        """
        Initialize a form env, if the document has forms. If already initialized, nothing will be done.
        See the :attr:`formenv` attribute.
    
        Note:
            If form rendering is desired, this method should be called directly after constructing the document,
            before getting any page handles (due to PDFium's API).
        
        Parameters:
            config (FPDF_FORMFILLINFO | None):
                Custom form config interface to use (optional).
        """
        
        formtype = self.get_formtype()
        if formtype == pdfium_c.FORMTYPE_NONE or self.formenv:
            return
        
        # safety check for older binaries to prevent a segfault (could be removed at some point)
        # https://github.com/bblanchon/pdfium-binaries/issues/105
        if "V8" in PDFIUM_INFO.flags and PDFIUM_INFO.origin != "sourcebuild" and PDFIUM_INFO.build <= 5677:
            raise RuntimeError("V8 enabled pdfium-binaries builds <= 5677 crash on init_forms().")
        
        if not config:
            if "XFA" in PDFIUM_INFO.flags:
                js_platform = pdfium_c.IPDF_JSPLATFORM(version=3)
                config = pdfium_c.FPDF_FORMFILLINFO(version=2, xfa_disabled=False, m_pJsPlatform=ctypes.pointer(js_platform))
            else:
                config = pdfium_c.FPDF_FORMFILLINFO(version=2)
        
        raw = pdfium_c.FPDFDOC_InitFormFillEnvironment(self, config)
        if not raw:
            raise PdfiumError(f"Initializing form env failed for document {self}.")
        self.formenv = PdfFormEnv(raw, config, self)
        self._add_kid(self.formenv)
        
        if formtype in (pdfium_c.FORMTYPE_XFA_FULL, pdfium_c.FORMTYPE_XFA_FOREGROUND):
            if "XFA" in PDFIUM_INFO.flags:
                ok = pdfium_c.FPDF_LoadXFA(self)
                if not ok:
                    err = pdfium_c.FPDF_GetLastError()
                    logger.warning(f"FPDF_LoadXFA() failed with {pdfium_i.XFAErrorToStr.get(err)}")
            else:
                logger.warning(
                    "init_forms() called on XFA pdf, but this pdfium binary was compiled without XFA support.\n"
                    "Run `PDFIUM_PLATFORM=auto-v8 pip install -v pypdfium2 --no-binary pypdfium2` to get a build with XFA support."
                )
    
    
    # TODO?(v5) consider cached property
    def get_formtype(self):
        """
        Returns:
            int: PDFium form type that applies to the document (:attr:`FORMTYPE_*`).
            :attr:`FORMTYPE_NONE` if the document has no forms.
        """
        return pdfium_c.FPDF_GetFormType(self)
    
    
    # TODO?(v5) consider cached property
    def get_pagemode(self):
        """
        Returns:
            int: Page displaying mode (:attr:`PAGEMODE_*`).
        """
        return pdfium_c.FPDFDoc_GetPageMode(self)
    
    
    # TODO?(v5) consider cached property
    def is_tagged(self):
        """
        Returns:
            bool: Whether the document is tagged (cf. PDF 1.7, 10.7 "Tagged PDF").
        """
        return bool( pdfium_c.FPDFCatalog_IsTagged(self) )
    
    
    def save(self, dest, version=None, flags=pdfium_c.FPDF_NO_INCREMENTAL):
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
            buffer, need_close = open(dest, "wb"), True
        elif pdfium_i.is_buffer(dest, "w"):
            buffer, need_close = dest, False
        else:
            raise ValueError(f"Cannot save to '{dest}'")
        
        try:
            saveargs = (self, pdfium_i.get_bufwriter(buffer), flags)
            ok = pdfium_c.FPDF_SaveAsCopy(*saveargs) if version is None else pdfium_c.FPDF_SaveWithVersion(*saveargs, version)
            if not ok:
                raise PdfiumError("Failed to save document.")
        finally:
            if need_close:
                buffer.close()
    
    
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
        ok = pdfium_c.FPDF_GetFileVersion(self, version)
        if not ok:
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
        metadata = {k: self.get_metadata_value(k) for k in self.METADATA_KEYS}
        if skip_empty:
            metadata = {k: v for k, v in metadata.items() if v}
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
            raise PdfiumError(f"Failed to get attachment at index {index}.")
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
            raise PdfiumError(f"Failed to create new attachment '{name}'.")
        return PdfAttachment(raw_attachment, self)
    
    
    def del_attachment(self, index):
        """
        Unlink the attachment at *index* (zero-based).
        It will be hidden from the viewer, but is still present in the file (as of PDFium 5418).
        Following attachments shift one slot to the left in the array representation used by PDFium's API.
        
        Handles to the attachment in question received from :meth:`.get_attachment`
        must not be accessed anymore after this method has been called.
        """
        ok = pdfium_c.FPDFDoc_DeleteAttachment(self, index)
        if not ok:
            raise PdfiumError(f"Failed to delete attachment at index {index}.")
    
    
    # TODO deprecate in favour of index access?
    def get_page(self, index):
        """
        Returns:
            PdfPage: The page at *index* (zero-based).
        Note:
            This calls ``FORM_OnAfterLoadPage()`` if the document has an active form env.
            The form env must not be closed before the page is closed!
        """
        
        raw_page = pdfium_c.FPDF_LoadPage(self, index)
        if not raw_page:
            raise PdfiumError("Failed to load page.")
        page = PdfPage(raw_page, self, self.formenv)
        
        if self.formenv:
            pdfium_c.FORM_OnAfterLoadPage(page, self.formenv)
            self.formenv._add_kid(page)
        else:
            self._add_kid(page)
        
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
        page = PdfPage(raw_page, self, None)
        # not doing formenv calls for new pages as we don't see the point
        self._add_kid(page)
        return page
    
    
    def del_page(self, index):
        """
        Remove the page at *index* (zero-based).
        """
        # FIXME what if the caller still has a handle to the page?
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
            ok = pdfium_c.FPDF_ImportPages(self, pdf, pages.encode("ascii"), index)
        else:
            page_count = 0
            c_pages = None
            if pages:
                page_count = len(pages)
                c_pages = (ctypes.c_int * page_count)(*pages)
            ok = pdfium_c.FPDF_ImportPagesByIndex(self, pdf, c_pages, page_count, index)
        
        if not ok:
            raise PdfiumError("Failed to import pages.")
    
    
    def get_page_size(self, index):
        """
        Returns:
            (float, float): Width and height in PDF canvas units of the page at *index* (zero-based).
        """
        size = pdfium_c.FS_SIZEF()
        ok = pdfium_c.FPDF_GetPageSizeByIndexF(self, index, size)
        if not ok:
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
            raise PdfiumError(f"Failed to capture page at index {index} as FPDF_XOBJECT.")
        xobject = PdfXObject(raw=raw_xobject, pdf=dest_pdf)
        self._add_kid(xobject)
        return xobject
    
    
    # TODO(apibreak) consider switching to a wrapper class around the raw bookmark
    # (either with getter methods, or possibly cached properties)
    def _get_bookmark(self, bookmark, level):
        
        n_bytes = pdfium_c.FPDFBookmark_GetTitle(bookmark, None, 0)
        buffer = ctypes.create_string_buffer(n_bytes)
        pdfium_c.FPDFBookmark_GetTitle(bookmark, buffer, n_bytes)
        title = buffer.raw[:n_bytes-2].decode('utf-16-le')
        
        # TODO(apibreak) just expose count as-is rather than using two variables and doing extra work
        count = pdfium_c.FPDFBookmark_GetCount(bookmark)
        is_closed = True if count < 0 else None if count == 0 else False
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
    
    
    # TODO(apibreak) change outline API (see above)
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
    
    
    def render(
            self,
            converter,
            renderer = PdfPage.render,
            page_indices = None,
            pass_info = False,
            n_processes = None,    # ignored, retained for compat
            mk_formconfig = None,  # ignored, retained for compat
            **kwargs
        ):
        """
        .. deprecated:: 4.19
            This method will be removed with the next major release due to serious issues rooted in the original API design. Use :meth:`.PdfPage.render()` instead.
            *Note that the CLI provides parallel rendering using a proper caller-side process pool with inline saving in rendering jobs.*
        
        .. versionchanged:: 4.25
            Removed the original process pool implementation and turned this into a wrapper for linear rendering, due to the serious conceptual issues and possible memory load escalation, especially with expensive receiving code (e.g. PNG encoding) or long documents. See the changelog for more info
        """
        
        warnings.warn("The document-level pdf.render() API is deprecated and uncored due to serious issues in the original concept. Use page.render() and a caller-side loop or process pool instead.", category=DeprecationWarning)
        
        if not page_indices:
            page_indices = [i for i in range(len(self))]
        for i in page_indices:
            bitmap = renderer(self[i], **kwargs)
            if pass_info:
                yield (converter(bitmap), bitmap.get_info())
            else:
                yield converter(bitmap)


class PdfFormEnv (pdfium_i.AutoCloseable):
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
        self.raw, self.config, self.pdf = raw, config, pdf
        super().__init__(PdfFormEnv._close_impl, self.config, self.pdf)
    
    @property
    def parent(self):  # AutoCloseable hook
        return self.pdf
    
    @staticmethod
    def _close_impl(raw, config, pdf):
        pdfium_c.FPDFDOC_ExitFormFillEnvironment(raw)
        id(config)
        pdf.formenv = None


class PdfXObject (pdfium_i.AutoCloseable):
    """
    XObject helper class.
    
    Attributes:
        raw (FPDF_XOBJECT): The underlying PDFium XObject handle.
        pdf (PdfDocument): Reference to the document this XObject belongs to.
    """
    
    def __init__(self, raw, pdf):
        self.raw, self.pdf = raw, pdf
        super().__init__(pdfium_c.FPDF_CloseXObject)
    
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
        return PdfObject(  # not a child object (see above)
            raw = raw_pageobj,
            pdf = self.pdf,
        )


def _open_pdf(input_data, password, autoclose):
    
    to_hold, to_close = (), ()
    if password is not None:
        password = (password+"\x00").encode("utf-8")
    
    if isinstance(input_data, Path):
        pdf = pdfium_c.FPDF_LoadDocument((str(input_data)+"\x00").encode("utf-8"), password)
    elif isinstance(input_data, (bytes, ctypes.Array)):
        pdf = pdfium_c.FPDF_LoadMemDocument64(input_data, len(input_data), password)
        to_hold = (input_data, )
    elif pdfium_i.is_buffer(input_data, "r"):
        bufaccess, to_hold = pdfium_i.get_bufreader(input_data)
        if autoclose:
            to_close = (input_data, )
        pdf = pdfium_c.FPDF_LoadCustomDocument(bufaccess, password)
    else:
        raise TypeError(f"Invalid input type '{type(input_data).__name__}'")
    
    if pdfium_c.FPDF_GetPageCount(pdf) < 1:
        err_code = pdfium_c.FPDF_GetLastError()
        raise PdfiumError(f"Failed to load document (PDFium: {pdfium_i.ErrorToStr.get(err_code)}).")
    
    return pdf, to_hold, to_close


# TODO(apibreak) change outline API (see above)
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
