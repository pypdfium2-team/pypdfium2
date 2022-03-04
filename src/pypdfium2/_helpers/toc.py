# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
import logging
from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers.utilities import translate_viewmode

logger = logging.getLogger(__name__)


class OutlineItem:
    """
    An entry in the table of contents ("bookmark").
    
    Parameters:
        level (int):
            The number of parent items.
        title (str):
            String of the bookmark.
        page_index (int):
            Zero-based index of the page the bookmark is pointing to.
        view_mode (ViewMode):
            A mode defining how to interpret the coordinates of *view_pos*.
        view_pos (typing.Sequence[float]):
            Target position on the page the viewport should jump to. It is a sequence of float values in PDF points. Depending on *view_mode*, it can contain between 0 and 4 coordinates.
    """
    
    def __init__(
            self,
            level,
            title,
            page_index,
            view_mode,
            view_pos,
        ):
        self.level = level
        self.title = title
        self.page_index = page_index
        self.view_mode = view_mode
        self.view_pos = view_pos


def _get_toc_entry(pdf, bookmark, level):
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
    view_pos = (pdfium.FS_FLOAT * 4)()
    view_mode = pdfium.FPDFDest_GetView(dest, n_params, view_pos)
    view_pos = list(view_pos)[:n_params.value]
    view_mode = translate_viewmode(view_mode)
    
    return OutlineItem(
        level = level,
        title = title,
        page_index = page_index,
        view_mode = view_mode,
        view_pos = view_pos,
    )


def get_toc(
        pdf,
        parent = None,
        level = 0,
        max_depth = 15,
        seen = None,
    ):
    """
    Parse the outline ("table of contents") of a PDF document.
    
    Parameters:
        pdf (``FPDF_DOCUMENT``):
            The PDFium document of which to read the outline.
        max_depth (int):
            The maximum recursion depth to consider when analysing the table of contents.
    
    Yields:
        :class:`OutlineItem`
    """
    
    if level >= max_depth:
        return []
    
    bookmark = pdfium.FPDFBookmark_GetFirstChild(pdf, parent)
    
    if seen is None:
        seen = set()
    
    while bookmark:
        
        address = ctypes.addressof(bookmark.contents)
        if address in seen:
            logger.critical("A circular bookmark reference was detected whilst parsing the table of contents.")
            break
        else:
            seen.add(address)
        
        yield _get_toc_entry(pdf, bookmark, level)
        
        yield from get_toc(
            pdf,
            parent = bookmark,
            level = level + 1,
            max_depth = max_depth,
            seen = seen,
        )
        
        bookmark = pdfium.FPDFBookmark_GetNextSibling(pdf, bookmark)
