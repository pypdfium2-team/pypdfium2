# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause


class PdfiumError (RuntimeError):
    """
    An exception from the PDFium library.
    """
    pass


class LoadPdfError (PdfiumError):
    """
    Raised if ``FPDF_GetPageCount()`` returns a value less than 1.
    """
    pass


class LoadPageError (PdfiumError):
    """ Raised if PDFium fails to load a page. """
    pass


class PageIndexError (IndexError):
    """ Raised on the attempt to load an out-of-bounds page number. """
    pass


class RecusionLimitError (RuntimeError):
    """ Raised if a recursion depth limit is exceeded. """
    pass
