# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.misc import raise_error


class BufferDataHolder:
    
    def __init__(self, reader_func, buffer, autoclose):
        self.reader_func = reader_func
        self.buffer = buffer
        self.autoclose = autoclose
    
    def close(self):
        id(self.reader_func)
        if self.autoclose:
            self.buffer.close()
        else:
            id(self.buffer)


class ByteDataHolder:
    
    def __init__(self, bytedata):
        self.bytedata = bytedata
    
    def close(self):
        id(self.bytedata)


class ReaderClass:
    
    def __init__(self, buffer):
        self._buffer = buffer
    
    def __call__(self, _, position, p_buf, size):
        c_buf = (ctypes.c_char * size).from_address( ctypes.addressof(p_buf.contents) )
        self._buffer.seek(position)
        self._buffer.readinto(c_buf)
        return 1


def is_input_buffer(maybe_buffer):
    if all( callable(getattr(maybe_buffer, a, None)) for a in ('seek', 'tell', 'readinto') ):
        return True
    else:
        return False


def open_pdf_buffer(buffer, password=None, autoclose=False):
    
    buffer.seek(0, 2)
    file_len = buffer.tell()
    buffer.seek(0)
    
    FuncType = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(None), ctypes.c_ulong, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_ulong)
    
    fileaccess = pdfium.FPDF_FILEACCESS()
    fileaccess.m_FileLen = file_len
    fileaccess.m_GetBlock = FuncType( ReaderClass(buffer) )
    
    pdf = pdfium.FPDF_LoadCustomDocument(ctypes.byref(fileaccess), password)
    ld_data = BufferDataHolder(
        reader_func = fileaccess.m_GetBlock,
        buffer = buffer,
        autoclose = autoclose,
    )
    
    return pdf, ld_data


def open_pdf_bytes(bytedata, password=None):
    pdf = pdfium.FPDF_LoadMemDocument(bytedata, len(bytedata), password)
    ld_data = ByteDataHolder(bytedata)
    return pdf, ld_data


def open_pdf(input_data, password=None, autoclose=False):
    
    ld_data = None
    if isinstance(input_data, str):
        pdf = pdfium.FPDF_LoadDocument(input_data, password)
    elif isinstance(input_data, bytes):
        pdf, ld_data = open_pdf_bytes(input_data, password)
    elif is_input_buffer(input_data):
        pdf, ld_data = open_pdf_buffer(input_data, password, autoclose)
    else:
        raise TypeError("The input must be a file path string, bytes, or a byte buffer, but '%s' was given." % type(input_data).__name__)
    
    if pdfium.FPDF_GetPageCount(pdf) < 1:
        raise_error("Loading the document failed")
    
    return pdf, ld_data
