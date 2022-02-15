# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
from PIL import Image
from typing import (
    Tuple,
    Sequence,
    Iterator,
    Union,
    BinaryIO,
)
import concurrent.futures
from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers.opener import PdfContext
from pypdfium2._helpers.constants import OptimiseMode
from pypdfium2._helpers.utilities import colour_as_hex
from pypdfium2._helpers.page_renderer import render_page


def _process_page(
        input_obj,
        index,
        password,
        scale,
        rotation,
        colour,
        annotations,
        greyscale,
        optimise_mode,
    ) -> Tuple[int, Image.Image]:
    
    with PdfContext(input_obj, password) as pdf:
        pil_image = render_page(
            pdf, index,
            scale = scale,
            rotation = rotation,
            colour = colour,
            annotations = annotations,
            greyscale = greyscale,
            optimise_mode = optimise_mode,
        )
    
    return index, pil_image


def _invoke_process_page(args):
    return _process_page(*args)


def render_pdf(
        input_obj: Union[str, bytes, BinaryIO],
        page_indices: list = None,
        password: str = None,
        n_processes: int = os.cpu_count(),
        scale: float = 1,
        rotation: int = 0,
        colour: Union[int, Sequence[int], None] = 0xFFFFFFFF,
        annotations: bool = True,
        greyscale: bool = False,
        optimise_mode: OptimiseMode = OptimiseMode.none,
    ) -> Iterator[ Tuple[Image.Image, str] ]:
    """
    Render multiple pages of a PDF document, using a process pool executor.
    
    Parameters:
        input_obj:
            The PDF document to render. It may be given as file path, bytes, or byte buffer.
        page_indices:
            A list of zero-based page indices to render.
        colour:
            The background colour to use, as a hexadecimal integer in 32-bit ARGB format.
            It is also possible to provide a colour tuple, which is implicitly converted
            using :func:`.colour_as_hex`.
    
    The other parameters are the same as for :func:`.render_page`.
    
    Yields:
        A PIL image, and a string for serial enumeration of output files.
    """
    
    if isinstance(colour, (tuple, list)):
        if len(colour) not in (3, 4):
            raise ValueError("If colour is given as a sequence, it must have length 3 or 4.")
        colour = colour_as_hex(*colour)
    
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
