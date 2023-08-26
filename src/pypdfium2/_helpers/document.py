# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PdfDocument", "PdfFormEnv", "PdfXObject", "PdfBookmark", "PdfDest")

import sys
import ctypes
import logging
from pathlib import Path
try:
    from multiprocessing.shared_memory import SharedMemory
except ImportError:
    SharedMemory = None
    assert sys.version_info < (3, 8)

import pypdfium2.raw as pdfium_r
import pypdfium2.internal as pdfium_i
from pypdfium2.version import (
    V_LIBPDFIUM,
    V_BUILDNAME,
    V_PDFIUM_IS_V8,
)
from pypdfium2._helpers.misc import PdfiumError
from pypdfium2._helpers.page import PdfPage
from pypdfium2._helpers.pageobjects import PdfObject
from pypdfium2._helpers.attachment import PdfAttachment

logger = logging.getLogger(__name__)


# TODO rollback: remove support for non-native input types. Handle them in the CLI instead.

class PdfDocument (pdfium_i.AutoCloseable):
    """
    Document helper class.
    
    Parameters:
        
        input (pathlib.Path | str | typing.BinaryIO | ~mmap.mmap | ctypes.Array | bytes | bytearray | memoryview | ~multiprocessing.shared_memory.SharedMemory | FPDF_DOCUMENT | typing.Callable):
            The input PDF given as file path, byte buffer, bytes-like object, raw PDFium document handle, or wrapper around another supported object (see the type definition above).
            Native support is available for :class:`~pathlib.Path`, byte buffers, :class:`bytes` and :class:`ctypes.Array`.
            The other input types are resolved to these, as far as possible.
            In this context, "byte buffer" refers to an object implementing ``seek() tell() (readinto() | read())`` in a :class:`~io.BufferedIOBase` like fashion.
            Buffers that do not provide ``readinto()`` fall back to ``read()`` and :func:`~ctypes.memmove`.
            Memory maps are currently treated as buffer (including SharedMemory, which is supported through the underlying mmap). Convert to a ctypes array on the caller side if handling as bytes-like object is desired instead.
        
        password (str | None):
            A password to unlock the PDF, if encrypted. Otherwise, None or an empty string may be passed.
            If a password is given but the PDF is not encrypted, it will be ignored (as of PDFium 5418).
        
        autoclose (bool):
            Whether byte buffer input should be automatically closed on finalization.
            If True and the input is shared memory, it will be closed but not destroyed.
        
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
            Form env, if :meth:`.init_forms` was called and the document has forms.
    """
    
    def __init__(self, input, password=None, autoclose=False):
        
        # CONSIDER adding a public method to inject into data_holder/data_closer
        
        self._orig_input = input
        self._autoclose = autoclose
        self._data_holder = []
        self._data_closer = []
        
        self._input, to_close = _preprocess_input(self._orig_input)
        if autoclose:
            self._data_closer.extend(to_close)
        
        self.formenv = None
        if isinstance(self._input, pdfium_r.FPDF_DOCUMENT):
            self.raw = self._input
        else:
            self.raw, to_hold, to_close = _open_pdf(self._input, password)
            self._data_holder.extend(to_hold)
            if autoclose:
                self._data_closer.extend(to_close)
        
        super().__init__(PdfDocument._close_impl, self._data_holder, self._data_closer)
    
    
    # TODO improve to show all input stages
    def __repr__(self):
        orig_in = self._orig_input
        if isinstance(orig_in, Path):
            input_r = repr( str(orig_in) )
        elif isinstance(orig_in, (bytes, bytearray, memoryview)):
            input_r = f"<{type(orig_in).__name__} at {hex(id(orig_in))}>"
        elif isinstance(orig_in, pdfium_r.FPDF_DOCUMENT):
            input_r = f"<FPDF_DOCUMENT at {hex(id(orig_in))}>"
        elif callable(orig_in):
            input_r = f"<callable at {hex(id(orig_in))}: {type(self._input).__name__}>"
        else:
            input_r = repr(self._input)
        return f"{super().__repr__()[:-1]} from {input_r}>"
    
    
    @property
    def parent(self):  # AutoCloseable hook
        return None
    
    
    @staticmethod
    def _close_impl(raw, data_holder, data_closer):
        pdfium_r.FPDF_CloseDocument(raw)
        
        for data in data_holder:
            id(data)
        data_holder.clear()
        
        for to_call in data_closer:
            to_call()  # TODO autoclose debug prints?
        data_closer.clear()
    
    
    def __len__(self):
        return pdfium_r.FPDF_GetPageCount(self)
    
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
        new_pdf = pdfium_r.FPDF_CreateNewDocument()
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
        if formtype == pdfium_r.FORMTYPE_NONE or self.formenv:
            return
        
        # safety check for older binaries to prevent a segfault (could be removed at some point)
        # https://github.com/bblanchon/pdfium-binaries/issues/105
        if V_PDFIUM_IS_V8 and int(V_LIBPDFIUM) <= 5677 and V_BUILDNAME == "pdfium-binaries":
            raise RuntimeError("V8 enabled pdfium-binaries builds <= 5677 crash on init_forms().")
        
        if not config:
            if V_PDFIUM_IS_V8:
                js_platform = pdfium_r.IPDF_JSPLATFORM(version=3)
                config = pdfium_r.FPDF_FORMFILLINFO(version=2, xfa_disabled=False, m_pJsPlatform=ctypes.pointer(js_platform))
            else:
                config = pdfium_r.FPDF_FORMFILLINFO(version=2)
        
        raw = pdfium_r.FPDFDOC_InitFormFillEnvironment(self, config)
        if not raw:
            raise PdfiumError(f"Initializing form env failed for document {self}.")
        self.formenv = PdfFormEnv(raw, config, self)
        self._add_kid(self.formenv)
        
        if formtype in (pdfium_r.FORMTYPE_XFA_FULL, pdfium_r.FORMTYPE_XFA_FOREGROUND):
            if V_PDFIUM_IS_V8:
                ok = pdfium_r.FPDF_LoadXFA(self)
                if not ok:
                    err = pdfium_r.FPDF_GetLastError()
                    logger.warning(f"FPDF_LoadXFA() failed with {pdfium_i.XFAErrorToStr.get(err)}")
            else:
                logger.warning(
                    "init_forms() called on XFA pdf, but this pdfium binary was compiled without XFA support.\n"
                    "Run `PDFIUM_BINARY=auto-v8 pip install -v pypdfium2 --no-binary pypdfium2` to get a build with XFA support."
                )
    
    
    def get_formtype(self):
        """
        Returns:
            int: PDFium form type that applies to the document (:attr:`FORMTYPE_*`).
            :attr:`FORMTYPE_NONE` if the document has no forms.
        """
        return pdfium_r.FPDF_GetFormType(self)
    
    
    def get_pagemode(self):
        """
        Returns:
            int: Page displaying mode (:attr:`PAGEMODE_*`).
        """
        return pdfium_r.FPDFDoc_GetPageMode(self)
    
    
    def is_tagged(self):
        """
        Returns:
            bool: Whether the document is tagged (cf. PDF 1.7, 10.7 "Tagged PDF").
        """
        return bool( pdfium_r.FPDFCatalog_IsTagged(self) )
    
    
    def save(self, dest, version=None, flags=pdfium_r.FPDF_NO_INCREMENTAL):
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
            ok = pdfium_r.FPDF_SaveAsCopy(*saveargs) if version is None else pdfium_r.FPDF_SaveWithVersion(*saveargs, version)
            if not ok:
                raise PdfiumError("Failed to save document.")
        finally:
            if need_close:
                buffer.close()
    
    
    def get_identifier(self, type=pdfium_r.FILEIDTYPE_PERMANENT):
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
        n_bytes = pdfium_r.FPDF_GetFileIdentifier(self, type, None, 0)
        buffer = ctypes.create_string_buffer(n_bytes)
        pdfium_r.FPDF_GetFileIdentifier(self, type, buffer, n_bytes)
        return buffer.raw[:n_bytes-2]
    
    
    def get_version(self):
        """
        Returns:
            int | None: The PDF version of the document (14 for 1.4, 15 for 1.5, ...),
            or None if the document is new or its version could not be determined.
        """
        version = ctypes.c_int()
        ok = pdfium_r.FPDF_GetFileVersion(self, version)
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
        n_bytes = pdfium_r.FPDF_GetMetaText(self, enc_key, None, 0)
        buffer = ctypes.create_string_buffer(n_bytes)
        pdfium_r.FPDF_GetMetaText(self, enc_key, buffer, n_bytes)
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
        return pdfium_r.FPDFDoc_GetAttachmentCount(self)
    
    
    def get_attachment(self, index):
        """
        Returns:
            PdfAttachment: The attachment at *index* (zero-based).
        """
        raw_attachment = pdfium_r.FPDFDoc_GetAttachment(self, index)
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
        enc_name_ptr = ctypes.cast(enc_name, pdfium_r.FPDF_WIDESTRING)
        raw_attachment = pdfium_r.FPDFDoc_AddAttachment(self, enc_name_ptr)
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
        ok = pdfium_r.FPDFDoc_DeleteAttachment(self, index)
        if not ok:
            raise PdfiumError(f"Failed to delete attachment at index {index}.")
    
    
    # CONSIDER deprecating in favour of index access?
    def get_page(self, index):
        """
        Returns:
            PdfPage: The page at *index* (zero-based).
        Note:
            This calls ``FORM_OnAfterLoadPage()`` if the document has an active form env.
            The form env must not be closed before the page is closed!
        """
        
        raw_page = pdfium_r.FPDF_LoadPage(self, index)
        if not raw_page:
            raise PdfiumError("Failed to load page.")
        page = PdfPage(raw_page, self, self.formenv)
        
        if self.formenv:
            pdfium_r.FORM_OnAfterLoadPage(page, self.formenv)
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
        raw_page = pdfium_r.FPDFPage_New(self, index, width, height)
        page = PdfPage(raw_page, self, None)
        # not doing formenv calls for new pages as it does not seem necessary
        self._add_kid(page)
        return page
    
    
    def del_page(self, index):
        """
        Remove the page at *index* (zero-based).
        """
        # FIXME what if the caller still has a handle to the page?
        pdfium_r.FPDFPage_Delete(self, index)
    
    
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
            ok = pdfium_r.FPDF_ImportPages(self, pdf, (pages+"\x00").encode("ascii"), index)
        else:
            page_count = 0
            c_pages = None
            if pages:
                page_count = len(pages)
                c_pages = (ctypes.c_int * page_count)(*pages)
            ok = pdfium_r.FPDF_ImportPagesByIndex(self, pdf, c_pages, page_count, index)
        
        if not ok:
            raise PdfiumError("Failed to import pages.")
    
    
    def get_page_size(self, index):
        """
        Returns:
            (float, float): Width and height in PDF canvas units of the page at *index* (zero-based).
        """
        size = pdfium_r.FS_SIZEF()
        ok = pdfium_r.FPDF_GetPageSizeByIndexF(self, index, size)
        if not ok:
            raise PdfiumError("Failed to get page size by index.")
        return (size.width, size.height)
    
    
    def get_page_label(self, index):
        """
        Returns:
            str: Label of the page at *index* (zero-based).
            (A page label is essentially an alias that may be displayed instead of the page number.)
        """
        n_bytes = pdfium_r.FPDF_GetPageLabel(self, index, None, 0)
        buffer = ctypes.create_string_buffer(n_bytes)
        pdfium_r.FPDF_GetPageLabel(self, index, buffer, n_bytes)
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
        raw_xobject = pdfium_r.FPDF_NewXObjectFromPage(dest_pdf, self, index)
        if raw_xobject is None:
            raise PdfiumError(f"Failed to capture page at index {index} as FPDF_XOBJECT.")
        xobject = PdfXObject(raw=raw_xobject, pdf=dest_pdf)
        self._add_kid(xobject)
        return xobject
    
    
    def get_toc(
            self,
            max_depth = 15,
            parent = None,
            level = 0,
            seen = None,
        ):
        """
        Iterate through the bookmarks in the document's table of contents (TOC).
        
        Parameters:
            max_depth (int):
                Maximum recursion depth to consider.
        Yields:
            :class:`.PdfBookmark`
        """
        
        # CONSIDER warn if max_depth reached?
        
        if seen is None:
            seen = set()
        
        bookmark_ptr = pdfium_r.FPDFBookmark_GetFirstChild(self, parent)
        
        while bookmark_ptr:
            
            address = ctypes.addressof(bookmark_ptr.contents)
            if address in seen:
                logger.warning("A circular bookmark reference was detected whilst parsing the table of contents.")
                break
            else:
                seen.add(address)
            
            yield PdfBookmark(bookmark_ptr, self, level)
            if level < max_depth-1:
                yield from self.get_toc(max_depth=max_depth, parent=bookmark_ptr, level=level+1, seen=seen)
            
            bookmark_ptr = pdfium_r.FPDFBookmark_GetNextSibling(self, bookmark_ptr)


def _preprocess_input(input):
    to_close = []
    if callable(input):
        input = input()
    if isinstance(input, str):
        input = Path(input)
    if isinstance(input, Path):
        input = input.expanduser().resolve()
        if not input.is_file():
            raise FileNotFoundError(input)
    else:
        if SharedMemory and isinstance(input, SharedMemory):
            # currently the resolution path is shm -> memoryview -> mmap
            to_close.append(input.close)
            input = input.buf
        if isinstance(input, memoryview):
            input = input.obj
        # NOTE in theory it might be good to handle mmap as bytes-like object, at least for SharedMemory to avoid callbacks and data copying - however, we currently don't do this due to complications with views held on an mmap - see PR(237)
        if isinstance(input, bytearray):
            input = (ctypes.c_ubyte * len(input)).from_buffer(input)
    return input, to_close


def _open_pdf(input, password):
    
    to_hold, to_close = (), ()
    password = (password+"\x00").encode("utf-8") if password else None
    
    if isinstance(input, Path):
        pdf = pdfium_r.FPDF_LoadDocument((str(input)+"\x00").encode("utf-8"), password)
    elif isinstance(input, (bytes, ctypes.Array)):
        pdf = pdfium_r.FPDF_LoadMemDocument64(input, len(input), password)
        to_hold = (input, )
    elif pdfium_i.is_buffer(input, "r"):
        bufaccess, to_hold = pdfium_i.get_bufreader(input)
        to_close = (input.close, )
        pdf = pdfium_r.FPDF_LoadCustomDocument(bufaccess, password)
    else:
        raise TypeError(f"Invalid input type '{type(input).__name__}'")
    
    if pdfium_r.FPDF_GetPageCount(pdf) < 1:
        err_code = pdfium_r.FPDF_GetLastError()
        raise PdfiumError(f"Failed to load document (PDFium: {pdfium_i.ErrorToStr.get(err_code)}).")
    
    return pdf, to_hold, to_close


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
        pdfium_r.FPDFDOC_ExitFormFillEnvironment(raw)
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
        super().__init__(pdfium_r.FPDF_CloseXObject)
    
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
        raw_pageobj = pdfium_r.FPDF_NewFormObjectFromXObject(self)
        return PdfObject(  # not a child object (see above)
            raw = raw_pageobj,
            pdf = self.pdf,
        )


class PdfBookmark (pdfium_i.AutoCastable):
    """
    Bookmark helper class.
    
    Attributes:
        raw (FPDF_BOOKMARK):
            The underlying PDFium bookmark handle.
        pdf (PdfDocument):
            Reference to the document this bookmark belongs to.
        level (int):
            The bookmark's nesting level in the TOC tree. Corresponds to the number of parent bookmarks.
    """
    
    def __init__(self, raw, pdf, level):
        self.raw, self.pdf, self.level = raw, pdf, level
    
    @property
    def parent(self):  # no hook, just for consistency
        return self.pdf
    
    def get_title(self):
        """
        Returns:
            str: The bookmark's title string.
        """
        n_bytes = pdfium_r.FPDFBookmark_GetTitle(self, None, 0)
        buffer = ctypes.create_string_buffer(n_bytes)
        pdfium_r.FPDFBookmark_GetTitle(self, buffer, n_bytes)
        return buffer.raw[:n_bytes-2].decode("utf-16-le")
    
    def get_count(self):
        """
        Returns:
            int: Signed number of child bookmarks (fully recursive). Zero if the bookmark has no descendants.
            The initial state shall be closed (collapsed) if negative, open (expanded) if positive.
        """
        return pdfium_r.FPDFBookmark_GetCount(self)
    
    def get_dest(self):
        """
        Returns:
            PdfDest | None: The bookmark's destination (page index, viewport), or None on failure.
        """
        raw_dest = pdfium_r.FPDFBookmark_GetDest(self.pdf, self)
        if not raw_dest:
            return None
        return PdfDest(raw_dest, pdf=self.pdf)


class PdfDest (pdfium_i.AutoCastable):
    """
    Destination helper class.
    
    Attributes:
        raw (FPDF_DEST): The underlying PDFium destination handle.
        pdf (PdfDocument): Reference to the document this dest belongs to.
    """
    
    def __init__(self, raw, pdf):
        self.raw, self.pdf = raw, pdf
    
    @property
    def parent(self):  # no hook, just for consistency
        return self.pdf
    
    def get_index(self):
        """
        Returns:
            int | None: Zero-based index of the page the dest points to, or None on failure.
        """
        val = pdfium_r.FPDFDest_GetDestPageIndex(self.pdf, self)
        return val if val >= 0 else None
    
    def get_view(self):
        """
        Returns:
            (int, list[float]): A tuple of (view_mode, view_pos).
            *view_mode* is a constant (one-of :data:`PDFDEST_VIEW_*`) defining how *view_pos* shall be interpreted.
            *view_pos* is the target position on the page the dest points to.
            It may contain between 0 to 4 float coordinates, depending on the view mode.
        """
        n_params = ctypes.c_ulong()
        pos = (pdfium_r.FS_FLOAT * 4)()
        mode = pdfium_r.FPDFDest_GetView(self, n_params, pos)
        pos = list(pos)[:n_params.value]
        return (mode, pos)
