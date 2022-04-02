# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause 

import ctypes
from pypdfium2 import _pypdfium as pdfium


class _writer_class:
    
    def __init__(self, buffer):
        self.buffer = buffer
        if not callable( getattr(self.buffer, 'write', None) ):
            raise ValueError("Output buffer must implement the write() method.")
    
    def __call__(self, _filewrite, data, size):
        block = ctypes.cast(data, ctypes.POINTER(ctypes.c_ubyte * size))
        self.buffer.write(block.contents)
        return 1


def save_pdf(pdf, buffer):
    """
    Write the data of a PDFium document into an output buffer.
    
    Parameters:
        pdf (``FPDF_DOCUMENT``):
            Handle to a PDFium document.
        buffer:
            A byte buffer to capture the data. It may be anything that implements the ``write()`` method.
    """
    
    WriteFunctype = ctypes.CFUNCTYPE(
        # restype
        ctypes.c_int,
        # argtypes
        ctypes.POINTER(pdfium.FPDF_FILEWRITE),
        ctypes.POINTER(None),
        ctypes.c_ulong,
    )
    
    filewrite = pdfium.FPDF_FILEWRITE()
    filewrite.WriteBlock = WriteFunctype( _writer_class(buffer) )
    
    pdfium.FPDF_SaveAsCopy(pdf, ctypes.byref(filewrite), pdfium.FPDF_NO_INCREMENTAL)
