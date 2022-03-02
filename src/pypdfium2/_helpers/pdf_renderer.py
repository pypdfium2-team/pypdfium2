# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import concurrent.futures
from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers.opener import PdfContext
from pypdfium2._helpers.constants import OptimiseMode
from pypdfium2._helpers.page_renderer import (
    render_page_tobytes,
    render_page_topil,
)


def _process_page(
        render_meth,
        input_obj,
        index,
        password,
        scale,
        rotation,
        colour,
        annotations,
        greyscale,
        optimise_mode,
    ):
    
    with PdfContext(input_obj, password) as pdf:
        result = render_meth(
            pdf, index,
            scale = scale,
            rotation = rotation,
            colour = colour,
            annotations = annotations,
            greyscale = greyscale,
            optimise_mode = optimise_mode,
        )
    
    return index, result


def _invoke_process_page(args):
    return _process_page(*args)


def _render_pdf_base(
        render_meth,
        input_obj,
        page_indices = None,
        password = None,
        n_processes = os.cpu_count(),
        scale = 1,
        rotation = 0,
        colour = (255, 255, 255, 255),
        annotations = True,
        greyscale = False,
        optimise_mode = OptimiseMode.none,
    ):
    
    with PdfContext(input_obj, password) as pdf:
        n_pages = pdfium.FPDF_GetPageCount(pdf)
    n_digits = len(str(n_pages))
    
    if page_indices is None or len(page_indices) == 0:
        page_indices = [i for i in range(n_pages)]
    elif any(i >= n_pages for i in page_indices):
        raise ValueError("Out of range page index detected.")
    
    meta_args = []
    for i in page_indices:
        sub_args = [
            render_meth,
            input_obj,
            i,
            password,
            scale,
            rotation,
            colour,
            annotations,
            greyscale,
            optimise_mode,
        ]
        meta_args.append(sub_args)
    
    with concurrent.futures.ProcessPoolExecutor(n_processes) as pool:
        for index, image in pool.map(_invoke_process_page, meta_args):
            suffix = str(index+1).zfill(n_digits)
            yield image, suffix


def render_pdf_tobytes(*args, **kws):
    """
    Render multiple pages of a PDF to bytes, using a process pool executor.
    
    Parameters:
        input_obj (str | bytes | typing.BinaryIO):
            The PDF document to render. It may be given as file path, bytes, or byte buffer.
        page_indices (typing.Sequence[int]):
            A list of zero-based page indices to render.
    
    The other parameters are the same as for :func:`.render_page_tobytes`.
    
    Yields:
        :class:`tuple`, :class:`str` – The return of :func:`.render_page_tobytes`, and a string for serial enumeration of output files.
    """
    yield from _render_pdf_base(render_page_tobytes, *args, **kws)


def render_pdf_topil(*args, **kws):
    """
    Render multiple pages of a PDF to :mod:`PIL` images. Similar to :func:`.render_pdf_tobytes`.
    
    Yields:
        :class:`PIL.Image.Image`, :class:`str`
    """
    yield from _render_pdf_base(render_page_topil, *args, **kws)
