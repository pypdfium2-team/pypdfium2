# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers.exceptions import *


def handle_pdfium_error(valid: bool = True) -> int:
    """
    Check the last PDFium error code and raise an exception accordingly.
    
    Parameters:
        valid:
            If :data:`False`, also raise an exception if ``FPDF_GetLastError()``
            returns ``FPDF_ERR_SUCCESS``.
    
    Returns:
        The error code as returned by PDFium.
    """
    
    last_error = pdfium.FPDF_GetLastError()
    
    if last_error == pdfium.FPDF_ERR_SUCCESS:
        if not valid:
            raise LoadPdfError("Even though no errors were reported, something invalid happened.")
    elif last_error == pdfium.FPDF_ERR_UNKNOWN:
        raise LoadPdfError("An unknown error occurred.")
    elif last_error == pdfium.FPDF_ERR_FILE:
        raise LoadPdfError("The file could not be found or opened.")
    elif last_error == pdfium.FPDF_ERR_FORMAT:
        raise LoadPdfError("Data format error.")
    elif last_error == pdfium.FPDF_ERR_PASSWORD:
        raise LoadPdfError("Missing or wrong password.")
    elif last_error == pdfium.FPDF_ERR_SECURITY:
        raise LoadPdfError("Unsupported security scheme.")
    elif last_error == pdfium.FPDF_ERR_PAGE:
        raise LoadPageError("Page not found or content error.")
    else:
        raise ValueError("Unknown PDFium error code {}.".format(last_error))
    
    return last_error
