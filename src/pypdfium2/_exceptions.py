# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0


class LoadPdfError (RuntimeError):
    """
    Raised if ``FPDF_GetPageCount()`` returns a value less than 1.
    """
    pass


class PageIndexError (IndexError):
    """ Raised on the attempt to load an out-of-bounds page number. """
    pass
