# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause


class PdfiumError (RuntimeError):
    """
    An exception from the PDFium library.
    """
    pass


class PageIndexError (IndexError):
    """ Raised on the attempt to load an out-of-bounds page number. """
    pass
