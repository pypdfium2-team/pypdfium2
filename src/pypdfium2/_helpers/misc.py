# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import enum
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers._utils import ErrorMapping


class OptimiseMode (enum.Enum):
    NONE = 0
    LCD_DISPLAY = 1
    PRINTING = 2


class OutlineItem:
    
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
    pass


def handle_error():
    
    err_code = pdfium.FPDF_GetLastError()
    if err_code == pdfium.FPDF_ERR_SUCCESS:
        return True
    
    err_message = ErrorMapping.get(err_code, "Error code %s" % err_code)
    raise PdfiumError(err_message)
