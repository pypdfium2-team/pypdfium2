# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# FIXME non-prefixed public members

__all__ = ["PdfiumError", "FileAccessMode", "RenderOptimizeMode"]

import enum


class PdfiumError (RuntimeError):
    """ An exception from the PDFium library, detected by function return code. """
    pass


class FileAccessMode (enum.Enum):
    """ File access modes. """
    NATIVE = 1  #: :func:`.FPDF_LoadDocument`       - Let PDFium manage file access in C/C++
    BUFFER = 2  #: :func:`.FPDF_LoadCustomDocument` - Pass data to PDFium incrementally from Python file buffer
    BYTES  = 3  #: :func:`.FPDF_LoadMemDocument64`  - Load data into memory and pass it to PDFium at once


class RenderOptimizeMode (enum.Enum):
    """ Page rendering optimization modes. """
    LCD_DISPLAY = 1  #: Optimize for LCD displays (via subpixel rendering).
    PRINTING    = 2  #: Optimize for printing.
