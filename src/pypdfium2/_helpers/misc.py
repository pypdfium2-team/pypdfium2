# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PdfiumError", "PdfiumWarning")


class PdfiumError (RuntimeError):
    """
    An error from the (Py)PDFium library.
    
    When a PDFium API indicates failure (as detected by function return code), this exception will be raised.
    
    Attributes:
        err_code (int | None):
            PDFium error code, for programmatic handling of error subtypes, if provided by the API in question.
            Currently, only document loading distinguishes between different errors, whereas most APIs just return error or success, in which case this field will be None.
    """
    
    def __init__(self, msg, err_code=None):
        super().__init__(msg)
        self.err_code = err_code


class PdfiumWarning (Warning):
    """
    A warning from the (Py)PDFium library.
    
    This is intended for error conditions that do not strictly necessitate raising an exception, but should still be exposed programmatically.
    
    Make sure you have configured the right warning level – otherwise, warnings might be hidden.
    
    Attributes:
        err_code (int | None):
            PDFium error code, for programmatic handling of error subtypes, if provided by the API in question. None otherwise.
            Currently, only XFA forms load failure provides this extra information.
    """
    
    def __init__(self, msg, err_code=None):
        super().__init__(msg)
        self.err_code = err_code
