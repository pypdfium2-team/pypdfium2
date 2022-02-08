# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause 

from pypdfium2._helpers import (
    opener,
    saver,
    toc,
    pdf_renderer,
    page_renderer,
)
from pypdfium2 import _pypdfium as pdfium


class PdfContext:
    """
    Context manager to open and automatically close again a PDFium document.
    
    Parameters:
        input_obj: The file or data to load using :func:`.open_pdf_auto`.
        password: A password to unlock the PDF, if encrypted.
    
    Returns:
        ``FPDF_DOCUMENT`` handle to the raw PDFium object.
    """
    
    def __init__(
            self,
            input_obj,
            password = None,
        ):
        self.input_obj = input_obj
        self.password = password
        self.ld_data = None
    
    def __enter__(self):
        self.pdf, self.ld_data = opener.open_pdf_auto(
            self.input_obj,
            password = self.password,
        )
        return self.pdf
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        opener.close_pdf(self.pdf, self.ld_data)


class PdfDocument:
    """
    Document class that maps the functional support model to an object-oriented API,
    unifying the separate helpers.
    
    Parameters:
        input_obj: The file or data to load using :func:`.open_pdf_auto`.
        password: A password to unlock the PDF, if encrypted.
    """
    
    def __init__(
            self,
            input_obj,
            password = None,
        ):
        self._input_obj = input_obj
        self._password = password
        self._pdf, self._ld_data = opener.open_pdf_auto(
            self._input_obj,
            password = self._password,
        )
    
    @property
    def raw(self):
        """ Get the raw PDFium ``FPDF_DOCUMENT`` handle. """
        return self._pdf
    
    def close(self):
        """
        Close the document to release allocated memory. This method must be called when
        done with processing the PDF.
        """
        return opener.close_pdf(self._pdf, self._ld_data)
    
    def save(self, *args, **kws):
        """
        Save the PDF into an output byte buffer (see :func:`.save_pdf`).
        """
        return saver.save_pdf(self._pdf, *args, **kws)
    
    def get_toc(self, max_depth=None):
        """
        Incrementally read the document's table of contents (see :func:`.get_toc`).
        """
        yield from toc.get_toc(
            self._pdf,
            max_depth = max_depth,
        )
    
    def render_pdf(self, **kwargs):
        """
        Incrementally render multiple pages (see :func:`.render_pdf`).
        """
        yield from pdf_renderer.render_pdf(
            self._input_obj,
            password = self._password,
            **kwargs
        )
    
    def render_page(self, index, **kwargs):
        """
        Render a single page (see :func:`.render_page`).
        """
        return page_renderer.render_page(
            self._pdf,
            page_index = index,
            **kwargs
        )
