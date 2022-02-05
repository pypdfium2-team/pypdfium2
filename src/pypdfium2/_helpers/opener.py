# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import sys
from os.path import abspath
from typing import (
    Union,
    Optional,
    BinaryIO,
)

from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers.nativeopener import *
from pypdfium2._helpers.error_handler import *


class PdfContext:
    """
    Context manager to open and automatically close again a PDFium document.
    It internally uses :func:`.open_pdf_auto` and :func:`.close_pdf`.
    This is the safest and most convenient way to open a document using PyPDFium2.
    
    Parameters:
        input_obj:
            File path to a PDF document, bytes, or a byte buffer.
        password:
            A password to unlock the document, if encrypted.
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
        self.pdf, self.ld_data = open_pdf_auto(self.input_obj, self.password)
        return self.pdf
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        close_pdf(self.pdf, self.ld_data)


def _str_isascii(string):
    try:
        tmp = string.encode('ascii')
    except UnicodeEncodeError:
        return False
    else:
        return True


def open_pdf_auto(
        input_obj: Union[str, bytes, BinaryIO],
        password: Union[str, bytes] = None,
    ) -> Tuple[pdfium.FPDF_DOCUMENT, Optional[LoaderData]]:
    """    
    Open a document from a file path or in-memory data. If you are not able to use the context
    manager :class:`PdfContext`, this is the recommended function to use for document opening.
    
    If the input is a regular file path, ``FPDF_LoadDocument()`` will be used.
    If on Windows, file paths that contain non-ascii characters will be loaded using
    :func:`.open_pdf_native`.
    If the input is bytes or a byte buffer, :func:`.open_pdf_bytes` will be used.
    
    Parameters:
        input_obj:
            File path to a PDF document, bytes, or a byte buffer.
        password:
            A password to unlock the document, if encrypted.
    
    Returns:
        The handle to a PDFium document, and a :class:`.LoaderData` object to store associated
        file access data.
    
    Warning:
        Callers **MUST** ensure that the :class:`LoaderData` object remain available for as
        long as they work with the PDF. This means it has to be accessed again when done with
        processing, to prevent Python from automatically deleting the object. This can be
        achieved by passing it as second parameter to :func:`.close_pdf`, which is also required
        to close the opened file buffer.
        If attempting to access the ``FPDF_DOCUMENT`` handle after the loader data has been deleted,
        a segmentation fault will occur.
    """
    
    if isinstance(input_obj, bytes):
        input_obj = io.BytesIO(input_obj)
    
    
    ld_data = None
    
    if isinstance(input_obj, str):
        if sys.platform.startswith('win32') and not _str_isascii(input_obj):
            pdf, ld_data = open_pdf_native(input_obj, password)
        else:
            pdf = pdfium.FPDF_LoadDocument(input_obj, password)
            if pdfium.FPDF_GetPageCount(pdf) < 1:
                handle_pdfium_error(False)
        
    elif is_buffer(input_obj):
        pdf, ld_data = open_pdf_buffer(input_obj, password)
        
    else:
        raise ValueError(
            "Input must be a file path, bytes or a byte buffer, but it is {}.".format( type(input_obj) )
        )
    
    return pdf, ld_data
    


def close_pdf(
        pdf: pdfium.FPDF_DOCUMENT,
        loader_data: LoaderData = None,
    ):
    """
    Close an in-memory PDFium document.
    
    Parameters:
        pdf:
            The PDFium document object to close using ``FPDF_CloseDocument()``.
        loader_data:
            A :class:`.LoaderData` object, as returned by :func:`.open_pdf_auto`,
            :func:`.open_pdf_buffer` or :func:`.open_pdf_native`.
    """
    pdfium.FPDF_CloseDocument(pdf)
    if loader_data is not None:
        loader_data.close()



def open_pdf(
        input_obj: Union[str, bytes, BinaryIO],
        password: Union[str, bytes] = None,
    ) -> pdfium.FPDF_DOCUMENT:
    """
    This function is deprecated and only included for backward compatibility.
    Please use :class:`.PdfContext` or :func:`.open_pdf_auto` instead.
    """
    
    filepath = None
    data = None
    
    if isinstance(input_obj, str):
        filepath = abspath(input_obj)
    elif isinstance(input_obj, bytes):
        data = input_obj
    elif callable(getattr(input_obj, 'read', None)):
        data = input_obj.read()
    else:
        raise ValueError(
            "Input must be a file path, bytes or a byte buffer, but it is {}.".format( type(input_obj) )
        )
    
    if (filepath is not None) and (data is None):
        pdf = pdfium.FPDF_LoadDocument(filepath, password)
    elif (data is not None) and (filepath is None):
        pdf = pdfium.FPDF_LoadMemDocument(data, len(data), password)
    else:
        assert False
    
    page_count = pdfium.FPDF_GetPageCount(pdf)
    if page_count < 1:
        handle_pdfium_error(False)
    
    return pdf
