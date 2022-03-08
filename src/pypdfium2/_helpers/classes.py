# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause 

from pypdfium2._helpers import (
    opener,
    saver,
    toc,
    pdf_renderer,
    page_renderer,
)


class PdfDocument:
    """
    Document class that maps the functional support model to an object-oriented API, unifying the separate helpers.
    
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
        Close the document to release allocated memory. This method must be called when done with processing the PDF.
        """
        return opener.close_pdf(self._pdf, self._ld_data)
    
    def save(self, *args, **kws):
        """
        Save the PDF into an output byte buffer (see :func:`.save_pdf`).
        """
        return saver.save_pdf(self._pdf, *args, **kws)
    
    def get_toc(self, **kws):
        """
        Incrementally read the document's table of contents (see :func:`.get_toc`).
        """
        yield from toc.get_toc(self._pdf, **kws)
    
    def render_page_tobytes(self, index, **kws):
        """
        Render a single page to bytes (see :func:`.render_page_tobytes`).
        """
        return page_renderer.render_page_tobytes(
            self._pdf,
            page_index = index,
            **kws
        )
    
    def render_pdf_tobytes(self, **kws):
        """
        Incrementally render multiple pages to bytes (see :func:`.render_pdf_tobytes`).
        """
        yield from pdf_renderer.render_pdf_tobytes(
            self._input_obj,
            password = self._password,
            **kws
        )
    
    def render_page_topil(self, index, **kws):
        """
        Render a single page to a :mod:`PIL` image (see :func:`.render_page_topil`).
        """
        return page_renderer.render_page_topil(
            self._pdf,
            page_index = index,
            **kws
        )
    
    def render_pdf_topil(self, **kws):
        """
        Incrementally render multiple pages to :mod:`PIL` images (see :func:`.render_pdf_topil`).
        """
        yield from pdf_renderer.render_pdf_topil(
            self._input_obj,
            password = self._password,
            **kws
        )
