# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers.nativeopener import (
    is_buffer,
    open_pdf_buffer,
)
from pypdfium2._helpers.error_handler import handle_pdfium_error


class PdfContext:
    """
    Context manager to open and automatically close again a PDFium document.
    
    Parameters:
        input_obj: The file or data to load using :func:`.open_pdf_auto`.
        password: A password to unlock the PDF, if encrypted.
    
    Returns:
        ``FPDF_DOCUMENT`` handle to the raw PDFium object.
    """
    
    def __init__(
            self,
            input_obj,
            password = None,
        ):
        self.input_obj = input_obj
        self.password = password
        self.ld_data = None
    
    def __enter__(self):
        self.pdf, self.ld_data = open_pdf_auto(
            self.input_obj,
            password = self.password,
        )
        return self.pdf
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        close_pdf(self.pdf, self.ld_data)


def open_pdf_auto(input_obj, password=None):
    """    
    Open a document from a file path or in-memory data.
    
    Parameters:
        input_obj (str | bytes | typing.BinaryIO):
            File path to a PDF document, bytes, or a byte buffer.
        password (typing.Optional[str | bytes]):
            A password to unlock the document, if encrypted.
    
    Returns:
        ``Tuple[pdfium.FPDF_DOCUMENT, Optional[LoaderDataHolder]]`` –
        The handle to a PDFium document, and optionally a loader data object to store associated buffer data.
    
    Warning:
        Callers **MUST** ensure that the loader data object remain available for as long as they work with the PDF. That means it has to be accessed again when done with processing, to prevent Python from automatically deleting the object. This can be achieved by passing it as second parameter to :func:`.close_pdf`, which is also necessary to release the acquired file buffer. If attempting to access the ``FPDF_DOCUMENT`` handle after the loader data has been deleted, a segmentation fault would occur.
    """
    
    ld_data = None
    if isinstance(input_obj, bytes):
        input_obj = io.BytesIO(input_obj)
    
    if isinstance(input_obj, str):
        # file path -> use FPDF_LoadDocument()
        pdf = pdfium.FPDF_LoadDocument(input_obj, password)
        if pdfium.FPDF_GetPageCount(pdf) < 1:
            handle_pdfium_error(False)
    elif is_buffer(input_obj):
        # byte buffer -> use open_pdf_buffer()
        pdf, ld_data = open_pdf_buffer(input_obj, password)
    else:
        raise ValueError("Input must be a file path, bytes or a byte buffer, but it is %s." % type(input_obj))
    
    return pdf, ld_data


def close_pdf(pdf, loader_data=None):
    """
    Close an in-memory PDFium document.
    
    Parameters:
        pdf (``FPDF_DOCUMENT``):
            The PDFium document object to close using ``FPDF_CloseDocument()``.
        loader_data (typing.Optional[LoaderDataHolder]):
            Object that stores custom file access data associated to the PDF.
    """
    
    pdfium.FPDF_CloseDocument(pdf)
    if loader_data is not None:
        loader_data.close()


def open_page(pdf, page_index):
    """
    Get a handle to the page at a certain index.
    
    Parameters:
        pdf (``FPDF_DOCUMENT``):
            PDFium document handle.
        page_index (int):
            Zero-based index of the page to load.
    
    Returns:
        ``FPDF_PAGE``
    """
    
    page_count = pdfium.FPDF_GetPageCount(pdf)
    if not 0 <= page_index < page_count:
        raise IndexError("Page index %s is out of bounds for document with %s pages." % (page_index, page_count))
    
    return pdfium.FPDF_LoadPage(pdf, page_index)
