# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.misc import (
    PdfiumError,
    ErrorToStr,
    DataHolder,
    is_input_buffer,
    get_fileaccess,
)


def open_pdf(input_data, password=None):
    
    if isinstance(password, str):
        password = password.encode("utf-8")
    
    ld_data = None
    if isinstance(input_data, str):
        pdf = pdfium.FPDF_LoadDocument(input_data.encode("utf-8"), password)
    elif isinstance(input_data, bytes):
        pdf = pdfium.FPDF_LoadMemDocument64(input_data, len(input_data), password)
        ld_data = DataHolder(input_data)
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
