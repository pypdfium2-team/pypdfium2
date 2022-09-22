# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.misc import (
    get_functype,
    PdfiumError,
    ErrorToStr,
)


class BufferDataHolder:
    
    def __init__(self, reader_func, buffer):
        self.reader_func = reader_func
        self.buffer = buffer
    
    def close(self):
        id(self.reader_func)
        id(self.buffer)


class ByteDataHolder:
    
    def __init__(self, bytedata):
        self.bytedata = bytedata
    
    def close(self):
        id(self.bytedata)


class _reader_class:
    
    def __init__(self, buffer):
        self._buffer = buffer
    
    def __call__(self, _, position, p_buf, size):
        c_buf = ctypes.cast(p_buf, ctypes.POINTER(ctypes.c_char * size))
        self._buffer.seek(position)
        self._buffer.readinto(c_buf.contents)
        return 1


def is_input_buffer(maybe_buffer):
    return all( callable(getattr(maybe_buffer, a, None)) for a in ("seek", "tell", "read", "readinto") )


def open_pdf_buffer(buffer, password=None):
    
    buffer.seek(0, 2)
    file_len = buffer.tell()
    buffer.seek(0)
    
    fileaccess = pdfium.FPDF_FILEACCESS()
    fileaccess.m_FileLen = file_len
    fileaccess.m_GetBlock = get_functype(pdfium.FPDF_FILEACCESS, "m_GetBlock")( _reader_class(buffer) )
    fileaccess.m_Param = None
    
    pdf = pdfium.FPDF_LoadCustomDocument(fileaccess, password)
    ld_data = BufferDataHolder(fileaccess.m_GetBlock, buffer)
    
    return pdf, ld_data


def open_pdf_bytes(bytedata, password=None):
    pdf = pdfium.FPDF_LoadMemDocument64(bytedata, len(bytedata), password)
    ld_data = ByteDataHolder(bytedata)
    return pdf, ld_data


def open_pdf(input_data, password=None):
    
    if isinstance(password, str):
        password = password.encode("utf-8")
    
    ld_data = None
    if isinstance(input_data, str):
        pdf = pdfium.FPDF_LoadDocument(input_data.encode("utf-8"), password)
    elif isinstance(input_data, bytes):
        pdf, ld_data = open_pdf_bytes(input_data, password)
    elif is_input_buffer(input_data):
        pdf, ld_data = open_pdf_buffer(input_data, password)
    else:
        raise TypeError("Invalid input type '%s'" % type(input_data).__name__)
    
    if pdfium.FPDF_GetPageCount(pdf) < 1:
        err_code = pdfium.FPDF_GetLastError()
        pdfium_msg = ErrorToStr.get(err_code, "Error code %s" % err_code)
        raise PdfiumError("Loading the document failed (PDFium: %s)" % pdfium_msg)
    
    return pdf, ld_data
