# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pypdfium2 import _pypdfium as pdfium


class PdfiumError (RuntimeError):
    """
    An exception from the PDFium library.
    """
    pass


def handle_pdfium_error(valid=True):
    """
    Check the last PDFium error code and raise an exception accordingly.
    
    Parameters:
        valid (bool):
            If :data:`False`, also raise an exception if ``FPDF_GetLastError()`` returns ``FPDF_ERR_SUCCESS``.
    
    Returns:
        :class:`int` – The error code as returned by PDFium.
    """
    
    last_error = pdfium.FPDF_GetLastError()
    
    if last_error == pdfium.FPDF_ERR_SUCCESS:
        if not valid:
            raise PdfiumError("Even though no errors were reported, something invalid happened.")
    elif last_error == pdfium.FPDF_ERR_UNKNOWN:
        raise PdfiumError("An unknown error occurred.")
    elif last_error == pdfium.FPDF_ERR_FILE:
        raise PdfiumError("The file could not be found or opened.")
    elif last_error == pdfium.FPDF_ERR_FORMAT:
        raise PdfiumError("Data format error.")
    elif last_error == pdfium.FPDF_ERR_PASSWORD:
        raise PdfiumError("Missing or wrong password.")
    elif last_error == pdfium.FPDF_ERR_SECURITY:
        raise PdfiumError("Unsupported security scheme.")
    elif last_error == pdfium.FPDF_ERR_PAGE:
        raise PdfiumError("Page not found or content error.")
    else:
        raise ValueError("Unknown PDFium error code {}.".format(last_error))
    
    return last_error
