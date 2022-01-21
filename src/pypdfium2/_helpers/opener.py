# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
from os.path import (
    abspath,
)
from typing import (
    Optional,
    Union,
)
from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers.error_handler import *


def open_pdf(
        file_or_data: Union[str, bytes, io.BytesIO, io.BufferedReader],
        password: Optional[ Union[str, bytes] ] = None
    ) -> pdfium.FPDF_DOCUMENT:
    """
    Open a PDFium document from a file path or in-memory data. When you have finished working
    with the document, call :func:`.close_pdf`.
    
    Parameters:
        
        file_or_data:
            
            The input PDF document, as file path or in-memory data.
            
            (On Windows, file paths with multi-byte characters don't work due to a
            `PDFium issue <https://bugs.chromium.org/p/pdfium/issues/detail?id=682>`_.)
        
        password:
            A password to unlock the document, if encrypted.
    
    Returns:
        ``FPDF_DOCUMENT``
    """
    
    filepath = None
    data = None
    
    if isinstance(file_or_data, str):
        filepath = abspath(file_or_data)
    elif isinstance(file_or_data, bytes):
        data = file_or_data
    elif isinstance(file_or_data, (io.BytesIO, io.BufferedReader)):
        data = file_or_data.read()
        file_or_data.seek(0)
    else:
        raise ValueError(
            "`file_or_data` must be a file path, bytes or a byte buffer, but it is {}.".format( type(file_or_data) )
        )
    
    if filepath is not None:
        pdf = pdfium.FPDF_LoadDocument(filepath, password)
    elif data is not None:
        pdf = pdfium.FPDF_LoadMemDocument(data, len(data), password)
    else:
        raise RuntimeError("Internal error: Neither data nor filepath set.")
    
    page_count = pdfium.FPDF_GetPageCount(pdf)
    if page_count < 1:
        handle_pdfium_error(False)
    
    return pdf


def close_pdf(pdf: pdfium.FPDF_DOCUMENT):
    """
    Close an in-memory PDFium document (alias for ``FPDF_CloseDocument()``).
    
    Parameters:
        pdf:
            The PDFium document object to close.
    """
    pdfium.FPDF_CloseDocument(pdf)


class PdfContext:
    """
    Context manager to open and automatically close again a PDFium document.
    
    Constructor parameters are the same as for :func:`open_pdf`.
    """
    
    def __init__(
            self,
            file_or_data,
            password = None,
        ):
        self.file_or_data = file_or_data
        self.password = password
    
    def __enter__(self):
        self.pdf = open_pdf(self.file_or_data, self.password)
        return self.pdf
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        close_pdf(self.pdf)
