# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import enum
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers._utils import ErrorMapping


class FileAccess (enum.Enum):
    """
    Different ways how files can be loaded.
    
    .. list-table:: Overview of file access modes
        :header-rows: 1
        :widths: auto
        
        * - Mode
          - PDFium loader
          - Comment
        * - :attr:`.NATIVE`
          - :func:`.FPDF_LoadDocument`
          - File access managed by PDFium in C/C++.
        * - :attr:`.BUFFER`
          - :func:`.FPDF_LoadCustomDocument`
          - Data read incrementally from Python file buffer.
        * - :attr:`.BYTES`
          - :func:`.FPDF_LoadMemDocument64`
          - Data loaded into memory and passed to PDFium at once.
    """
    NATIVE = 0
    BUFFER = 1
    BYTES  = 2


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
    """ An exception from the PDFium library, detected by function return code. """
    pass


def raise_error(msg):
    """
    Raise a :class:`.PdfiumError` annotated with the description of PDFium's current error code.
    
    Warning:
        This shall be called only if a PDFium call failed according to return code **and**
        :func:`.FPDF_GetLastError()` is mentioned in the documentation for the function in question.
        Currently, :func:`.raise_error` is only applicable to document loading APIs.
    
    Parameters:
        msg (str): The error message explaining the problem.
    """
    
    err_code = pdfium.FPDF_GetLastError()
    pdfium_msg = ErrorMapping.get(err_code, "Error code %s" % err_code)
    
    raise PdfiumError("%s (PDFium: %s)" % (msg, pdfium_msg))
