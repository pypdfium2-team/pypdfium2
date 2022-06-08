# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import enum
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers._utils import ErrorMapping


class FileAccess (enum.Enum):
    """ Different ways how files can be loaded. """
    NATIVE = 0  #: :func:`.FPDF_LoadDocument` - Let PDFium open the file in C/C++.
    BUFFER = 1  #: :func:`.FPDF_LoadCustomDocument` - Acquire a Python file buffer that is read incrementally by callback function.
    BYTES  = 2  #: :func:`.FPDF_LoadMemDocument` - Read the whole file into memory and pass the data to PDFium at once.


class OptimiseMode (enum.Enum):
    """ Modes defining how page rendering shall be optimised. """
    NONE = 0         #: No optimisation.
    LCD_DISPLAY = 1  #: Optimise for LCD displays (via subpixel rendering).
    PRINTING = 2     #: Optimise for printing.


class OutlineItem:
    """
    Class to store information about an entry in the table of contents ("bookmark").
    
    Parameters:
        level (int):
            Number of parent items.
        title (str):
            String of the bookmark.
        is_closed (bool):
            If :data:`True`, child items shall be hidden by default.
        page_index (int):
            Zero-based index of the page the bookmark points to.
        view_mode (int):
            A view mode constant (``PDFDEST_VIEW_...``) defining how the coordinates of *view_pos* shall be interpreted.
        view_pos (typing.Sequence[float]):
            Target position on the page the viewport should jump to when the bookmark is clicked.
            It is a sequence of :class:`float` values in PDF canvas units.
            Depending on *view_mode*, it can contain between 0 and 4 coordinates.
    """
    
    def __init__(
            self,
            level,
            title,
            is_closed,
            page_index,
            view_mode,
            view_pos,
        ):
        self.level = level
        self.title = title
        self.is_closed = is_closed
        self.page_index = page_index
        self.view_mode = view_mode
        self.view_pos = view_pos


class PdfiumError (RuntimeError):
    """ A PDFium exception forwarded by :func:`.raise_error` """
    pass


def raise_error(msg):
    """
    Raise a :class:`.PdfiumError` annotated with the description of PDFium's current error code.
    
    Note:
        This function shall be called if the return value of a PDFium call indicates failure.
    
    Parameters:
        msg (str): The error message explaining the problem.
    """
    
    err_code = pdfium.FPDF_GetLastError()
    pdfium_msg = ErrorMapping.get(err_code, "Error code %s" % err_code)
    
    raise PdfiumError("%s (PDFium: %s)" % (msg, pdfium_msg))
