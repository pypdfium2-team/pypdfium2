# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
import logging
import warnings
from typing import (
    Sequence,
    Optional,
    Iterator,
)
from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers.constants import ViewMode
from pypdfium2._helpers.utilities import translate_viewmode

logger = logging.getLogger(__name__)


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
            level: int,
            title: str,
            page_index: int,
            view_mode: ViewMode,
            view_pos: Sequence[float],
        ):
        self.level = level
        self.title = title
        self.page_index = page_index
        self.view_mode = view_mode
        self.view_pos = view_pos


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
    view_pos = (pdfium.FS_FLOAT * 4)()
    view_mode = pdfium.FPDFDest_GetView(dest, n_params, view_pos)
    n_params = n_params.value
    view_pos = list(view_pos)[:n_params]
    view_mode = translate_viewmode(view_mode)
    
    return OutlineItem(
        level = level,
        title = title,
        page_index = page_index,
        view_mode = view_mode,
        view_pos = view_pos,
    )


def get_toc(
        pdf: pdfium.FPDF_DOCUMENT,
        parent: Optional[pdfium.FPDF_BOOKMARK] = None,
        level: int = 0,
        max_depth: int = None,
        seen: Optional[set] = None,
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
    
    if max_depth is None:
        max_depth = 15
    
    if level >= max_depth:
        #logger.warning("Maximum recursion depth reached.")
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


def print_toc(toc) -> None:
    """
    This function is deprecated and scheduled for removal.
    Please use custom code to print the table of contents.
    """
    
    warnings.warn(
        "print_toc() is scheduled for removal - please use custom code instead.",
        DeprecationWarning
    )
    
    for item in toc:
        print(
            '    ' * item.level +
            "{} -> {}  # {} {}".format(
                item.title,
                item.page_index + 1,
                item.view_mode,
                item.view_pos,
            )
        )
