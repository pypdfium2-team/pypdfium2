# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PdfiumError", )


class PdfiumError (RuntimeError):
    """ An exception from the PDFium library, detected by function return code. """
    pass
