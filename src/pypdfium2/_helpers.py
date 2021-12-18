# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import os
import sys
import math
import ctypes
import logging
import pathlib
from PIL import Image
import concurrent.futures
from os.path import abspath
from typing import (
    Union,
    Optional,
    Sequence,
    Iterator,
    Tuple,
)

from pypdfium2._types import *
from pypdfium2._constants import *
from pypdfium2._exceptions import *
from pypdfium2 import _pypdfium as pdfium

logger = logging.getLogger(__name__)


def handle_pdfium_error(valid: bool = True) -> int:
    """
    Check the last PDFium error code and raise an exception accordingly.
    
    Parameters:
        valid:
            If :data:`False`, also raise an exception if ``FPDF_GetLastError``
            returns ``FPDF_ERR_SUCCESS``.
    
    Returns:
        The error code as returned by PDFium.
    """
    
    last_error = pdfium.FPDF_GetLastError()
    
    if last_error == pdfium.FPDF_ERR_SUCCESS:
        if not valid:
            raise LoadPdfError(f"Even though no errors were reported, something invalid happened.")
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
        raise ValueError(f"Unknown PDFium error code {last_error}.")
    
    return last_error


def open_pdf(
        file_or_data: Union[str, pathlib.Path, bytes, io.BytesIO, io.BufferedReader],
        password: Optional[ Union[str, bytes] ] = None
    ) -> pdfium.FPDF_DOCUMENT:
    """
    Open a PDFium document from a file path or in-memory data. When you have finished working
    with the document, call :func:`.close_pdf`.
    
    Parameters:
        
        file_or_data:
            The input PDF document, as file path or in-memory data.
            
            (On Windows, file paths with multi-byte characters don't work due to a
            `PDFium issue <https://bugs.chromium.org/p/pdfium/issues/detail?id=682>`_.)
        
        password:
            A password to unlock the document, if encrypted.
    
    Returns:
        ``FPDF_DOCUMENT``
    """
    
    filepath = None
    data = None
    
    if isinstance(file_or_data, str):
        filepath = abspath(file_or_data)
    elif isinstance(file_or_data, pathlib.Path):
        filepath = str(file_or_data.resolve())
    elif isinstance(file_or_data, bytes):
        data = file_or_data
    elif isinstance(file_or_data, (io.BytesIO, io.BufferedReader)):
        data = file_or_data.read()
        file_or_data.seek(0)
    else:
        raise ValueError(f"`file_or_data` must be a file path, bytes or a byte buffer, but it is {type(file_or_data)}.")
    
    if filepath is not None:
        pdf = pdfium.FPDF_LoadDocument(filepath, password)
    elif data is not None:
        pdf = pdfium.FPDF_LoadMemDocument(data, len(data), password)
    else:
        raise RuntimeError("Internal error: Neither data nor filepath set.")
    
    page_count = pdfium.FPDF_GetPageCount(pdf)
    if page_count < 1:
        handle_pdfium_error(False)
    
    return pdf


def close_pdf(pdf: pdfium.FPDF_DOCUMENT):
    """
    Close an in-memory PDFium document (alias for ``FPDF_CloseDocument()``).
    
    Parameters:
        pdf:
            The PDFium document object to close.
    """
    pdfium.FPDF_CloseDocument(pdf)


class PdfContext:
    """
    Context manager to open and automatically close again a PDFium document.
    
    Constructor parameters are the same as for :func:`open_pdf`.
    """
    
    def __init__(
            self,
            file_or_data,
            password = None,
        ):
        self.pdf = open_pdf(file_or_data, password)
    
    def __enter__(self):
        return self.pdf
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        close_pdf(self.pdf)


def _translate_rotation(rotation: int) -> int:
    """
    Convert a rotation value in degrees to a PDFium rotation constant.
    """
    
    if rotation == 0:
        return 0
    elif rotation == 90:
        return 1
    elif rotation == 180:
        return 2
    elif rotation == 270:
        return 3
    else:
        raise ValueError(f"Invalid rotation {rotation}")


def _hex_digits(c):
    
    hxc = hex(c)[2:]
    if len(hxc) == 1:
        hxc = "0" + hxc
    
    return hxc
    

def _colour_as_hex(r, g, b, a=255) -> int:
    """
    Convert a colour given as integers of ``red, green, blue, alpha`` ranging from 0 to 255
    to a single value in 8888 ARGB format.
    """
    
    colours = (a, r, g, b)
    
    for c in colours:
        assert isinstance(c, int)
        assert 0 <= c <= 255
    
    hxc_str = "0x"
    for c in colours:
        hxc_str += _hex_digits(c)
    
    hxc_int = int(hxc_str, 0)
    
    return hxc_int


def render_page(
        pdf: pdfium.FPDF_DOCUMENT,
        page_index: int = 0,
        *,
        scale: float = 1,
        rotation: int = 0,
        colour: Union[int, Sequence[int], None] = 0xFFFFFFFF,
        annotations: bool = True,
        greyscale: bool = False,
        optimise_mode: OptimiseMode = OptimiseMode.none,
    ) -> Image.Image:
    """
    Rasterise a single PDF page using PDFium.
    
    Parameters:
        
        pdf:
            A PDFium document (can be obtained with :class:`PdfContext` or :func:`open_pdf`).
        
        page_index:
            Zero-based index of the page to render.
        
        scale:
            
            Define the quality (or size) of the image.
            
            By default, one PDF point (1/72in) is rendered to 1x1 pixel. This factor scales the
            number of pixels that represent one point.
            
            Higher values increase quality, file size and rendering duration, while lower values
            reduce them.
            
            Note that UserUnit is not taken into account, so if you are using PyPDFium2 in
            conjunction with an other PDF library, you may want to check for a possible
            ``/UserUnit`` in the page dictionary and multiply this scale factor with it.
        
        rotation:
            Rotate the page by 90, 180, or 270 degrees. Value 0 means no rotation.
        
        colour:
            
            .. _8888 ARGB: https://en.wikipedia.org/wiki/RGBA_color_model#ARGB32
            
            Which background colour to use (defaults to white).
            It can either be given as a hexadecimal integer in `8888 ARGB`_ format, or as a
            4-value sequence of ``red, green, blue, alpha`` integers ranging from 0 to 255.
        
        annotations:
            Whether to render page annotations.
        
        greyscale:
            Whether to render in greyscale mode (no colours).
        
        optimise_mode:
            Optimise rendering for LCD displays or for printing.
    
    Returns:
        :class:`PIL.Image.Image`
    """
    
    use_alpha = True
    
    if isinstance(colour, (tuple, list)):
        
        if len(colour) == 3:
            use_alpha = False
        elif len(colour) == 4:
            if colour[3] == 255:
                use_alpha = False
        else:
            raise ValueError("If colour is given as a list, it must have length 3 or 4.")
        
        colour = _colour_as_hex(*colour)
        
    elif isinstance(colour, int):
        alpha_val = hex(colour)[2:4].upper()
        if alpha_val == 'FF':
            use_alpha = False
    
    page_count = pdfium.FPDF_GetPageCount(pdf)
    if not 0 <= page_index < page_count:
        raise PageIndexError(f"Page index {page_index} is out of bounds for document with {page_count} pages.")
    
    page = pdfium.FPDF_LoadPage(pdf, page_index)
    
    width  = math.ceil(pdfium.FPDF_GetPageWidthF(page)  * scale)
    height = math.ceil(pdfium.FPDF_GetPageHeightF(page) * scale)
    
    if rotation in (90, 270):
        width, height = height, width
    
    bitmap = pdfium.FPDFBitmap_Create(width, height, int(use_alpha))
    if colour is not None:
        pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, colour)
    
    render_flags = 0x00
    
    if annotations:
        render_flags |= pdfium.FPDF_ANNOT
    if greyscale:
        render_flags |= pdfium.FPDF_GRAYSCALE
    
    if optimise_mode is OptimiseMode.none:
        pass
    elif optimise_mode is OptimiseMode.lcd_display:
        render_flags |= pdfium.FPDF_LCD_TEXT
    elif optimise_mode is OptimiseMode.printing:
        render_flags |= pdfium.FPDF_PRINTING
    else:
        raise ValueError(f"Invalid optimise_mode {optimise_mode}")
    
    pdfium.FPDF_RenderPageBitmap(
        bitmap,
        page,
        0, 0,
        width, height,
        _translate_rotation(rotation),
        render_flags,
    )
    
    cbuffer = pdfium.FPDFBitmap_GetBuffer(bitmap)
    buffer = ctypes.cast(cbuffer, ctypes.POINTER(ctypes.c_ubyte * (width * height * 4)))
    
    pil_image = Image.frombuffer("RGBA", (width, height), buffer.contents, "raw", "BGRA", 0, 1)
    
    if greyscale:
        if use_alpha:
            pil_image = pil_image.convert("LA")
        else:
            pil_image = pil_image.convert("L")
    
    elif not use_alpha:
        pil_image = pil_image.convert("RGB")
    
    pdfium.FPDFBitmap_Destroy(bitmap)
    pdfium.FPDF_ClosePage(page)
    
    return pil_image


def _process_page(
        file_or_bytes,
        index,
        password,
        scale,
        rotation,
        colour,
        annotations,
        greyscale,
        optimise_mode,
    ) -> Tuple[int, Image.Image]:
    
    with PdfContext(file_or_bytes, password) as pdf:
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
        file_or_bytes: Union[str, bytes],
        page_indices: list = None,
        *,
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
        file_or_bytes:
            The PDF document to render, either given as file path or as bytes.
            On Windows, if the given file path contains non-ascii characters, the data
            is read into memory.
        page_indices:
            A list of zero-based page indices to render.
    
    The other parameters are the same as for :func:`render_page`.
    
    Yields:
        A PIL image, and a string for serial enumeration of output files.
    """
        
    if isinstance(file_or_bytes, str):
        if sys.platform.startswith('win32') and not file_or_bytes.isascii():
            with open(file_or_bytes, 'rb') as file_handle:
                data = file_handle.read()
            file_or_bytes = data
    
    with PdfContext(file_or_bytes, password) as pdf:
        n_pages = pdfium.FPDF_GetPageCount(pdf)
    n_digits = len(str(n_pages))
    
    if page_indices is None or len(page_indices) == 0:
        page_indices = [i for i in range(n_pages)]
    elif any(i >= n_pages for i in page_indices):
        raise ValueError("Out of range page index detected.")
    
    meta_args = []
    for i in page_indices:
        sub_args = [
            file_or_bytes,
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
            pageno = index + 1
            suffix = f"{pageno:0{n_digits}}"
            yield image, suffix


class OutlineItem:
    """
    An entry in the table of contents ("bookmark").
    
    Parameters:
        level:
            The number of parent items.
        title:
            String of the bookmark.
        page_index:
            Zero-based index of the page the bookmark is pointing to.
        view_mode:
            A mode defining how to interpret the coordinates of *view_pos*.
        view_pos:
            Target position on the page the viewport should jump to. It is a sequence of float values
            in PDF points. Depending on *view_mode*, it can contain between 0 and 4 coordinates.
    """
    
    def __init__(
            self,
            level: int = None,
            title: str = None,
            page_index: int = None,
            view_mode: ViewMode = None,
            view_pos: Sequence[float] = None,
        ):
        
        self.level = level
        self.title = title
        self.page_index = page_index
        self.view_mode = view_mode
        self.view_pos = view_pos


def _translate_viewmode(viewmode: int) -> ViewMode:
    """
    Convert a PDFium view mode integer to an attribute of the :class:`.ViewMode` enum.
    """
    
    if viewmode == pdfium.PDFDEST_VIEW_UNKNOWN_MODE:
        return ViewMode.Unknown
    elif viewmode == pdfium.PDFDEST_VIEW_XYZ:
        return ViewMode.XYZ
    elif viewmode == pdfium.PDFDEST_VIEW_FIT:
        return ViewMode.Fit
    elif viewmode == pdfium.PDFDEST_VIEW_FITH:
        return ViewMode.FitH
    elif viewmode == pdfium.PDFDEST_VIEW_FITV:
        return ViewMode.FitV
    elif viewmode == pdfium.PDFDEST_VIEW_FITR:
        return ViewMode.FitR
    elif viewmode == pdfium.PDFDEST_VIEW_FITB:
        return ViewMode.FitB
    elif viewmode == pdfium.PDFDEST_VIEW_FITBH:
        return ViewMode.FitBH
    elif viewmode == pdfium.PDFDEST_VIEW_FITBV:
        return ViewMode.FitBV


def _get_toc_entry(
        pdf: pdfium.FPDF_DOCUMENT,
        bookmark: pdfium.FPDF_BOOKMARK,
        level: int,
    ) -> OutlineItem:
    """
    Convert a raw PDFium bookmark to an :class:`.OutlineItem`.
    """
    
    # title
    t_buflen = pdfium.FPDFBookmark_GetTitle(bookmark, None, 0)
    t_buffer = ctypes.create_string_buffer(t_buflen)
    pdfium.FPDFBookmark_GetTitle(bookmark, t_buffer, t_buflen)
    title = t_buffer.raw[:t_buflen].decode('utf-16-le')[:-1]
    
    # page index
    dest = pdfium.FPDFBookmark_GetDest(pdf, bookmark)
    page_index = pdfium.FPDFDest_GetDestPageIndex(pdf, dest)
    
    # viewport
    n_params = ctypes.c_ulong()
    view_pos = ArrayFSFloat4()
    view_mode = pdfium.FPDFDest_GetView(dest, n_params, view_pos)
    n_params = n_params.value
    view_pos = list(view_pos)[:n_params]
    view_mode = _translate_viewmode(view_mode)
    
    item = OutlineItem()
    item.level = level
    item.title = title
    item.page_index = page_index
    item.view_mode = view_mode
    item.view_pos = view_pos
    
    return item


def get_toc(
        pdf: pdfium.FPDF_DOCUMENT,
        parent: Optional[pdfium.FPDF_BOOKMARK] = None,
        level: int = 0,
        max_depth: int = 15,
        seen: Optional[list] = None,
    ) -> Iterator[OutlineItem]:
    """
    Read the table of contents ("outline") of a PDF document.
    
    Parameters:
        pdf:
            The PDFium document of which to parse the ToC.
        max_depth:
            The maximum recursion depth to consider when analysing the outline.
        
    Yields:
        :class:`OutlineItem`
    """
    
    if level >= max_depth:
        raise RecusionLimitError(f"The maximum recursion level {max_depth} was exceeded.")
    
    bookmark = pdfium.FPDFBookmark_GetFirstChild(pdf, parent)
    
    if seen is None:
        seen = []
    
    while bookmark:
        
        address = ctypes.addressof(bookmark.contents)
        if address in seen:
            logger.critical("A circular bookmark reference was detected whilst parsing the table of contents.")
            break
        else:
            seen.append(address)
        
        item = _get_toc_entry(pdf, bookmark, level)
        yield item
        
        for child in get_toc(pdf, bookmark, level=level+1, max_depth=max_depth, seen=seen):
            yield child
        
        bookmark = pdfium.FPDFBookmark_GetNextSibling(pdf, bookmark)


def print_toc(toc) -> None:
    """
    Print the table of contents in a well-readable manner.
    
    Parameters:
        toc:
            The iterator of the outline to display (result of :func:`get_toc`).
    """
    
    for item in toc:
        
        level = item.level
        title = item.title
        pagenum = item.page_index + 1
        view_mode = item.view_mode
        view_pos = item.view_pos
        
        print('    '*level + f"{title} -> {pagenum}  # {view_mode} {view_pos}")
