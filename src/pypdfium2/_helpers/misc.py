# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import enum
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers._utils import ErrorMapping


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
        view_mode (``PDFDEST_VIEW_...``):
            A view mode constant defining how the coordinates of *view_pos* shall be interpreted.
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
    """ A PDFium exception forwarded by :func:`.handle_error` """
    pass


def handle_error():
    """
    Check the current error code provided by PDFium.
    If it indicates success, nothing will be done. Otherwise, a :class:`.PdfiumError` will be raised accordingly.
    
    Important:
        This error handler should only be called to determine the cause of a recent failure detected by return code.
        Otherwise, it could happen that a previously caught exception is re-raised.
    """
    
    err_code = pdfium.FPDF_GetLastError()
    if err_code == pdfium.FPDF_ERR_SUCCESS:
        return
    
    err_message = ErrorMapping.get(err_code, "Error code %s" % err_code)
    raise PdfiumError(err_message)
