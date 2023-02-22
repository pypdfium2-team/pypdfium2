# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
import logging
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c
from .conftest import TestResources


def _compare_bookmark(bookmark, view_pos, **kwargs):
    for name, exp_value in kwargs.items():
        assert exp_value == getattr(bookmark, name)
    assert pytest.approx(bookmark.view_pos, abs=1) == view_pos


def test_gettoc():
    
    pdf = pdfium.PdfDocument(TestResources.toc)
    toc = pdf.get_toc()
    
    # check first bookmark
    _compare_bookmark(
        next(toc),
        title = "One",
        page_index = 0,
        view_mode = pdfium_c.PDFDEST_VIEW_XYZ,
        view_pos = (89, 758, 0),
        is_closed = True,
        n_kids = 2,
    )
    
    # check common values
    for bookmark in toc:
        assert isinstance(bookmark, pdfium.PdfOutlineItem)
        assert bookmark.view_mode is pdfium_c.PDFDEST_VIEW_XYZ
        assert round(bookmark.view_pos[0]) == 89
    
    # check last bookmark
    _compare_bookmark(
        bookmark,
        title = "Three-B",
        page_index = 1,
        view_mode = pdfium_c.PDFDEST_VIEW_XYZ,
        view_pos = (89, 657, 0),
        is_closed = None,
        n_kids = 0,
    )


def test_gettoc_circular(caplog):
    
    pdf = pdfium.PdfDocument(TestResources.toc_circular)
    toc = pdf.get_toc()
    
    _compare_bookmark(
        next(toc),
        title = "A Good Beginning",
        page_index = None,
        view_mode = pdfium_c.PDFDEST_VIEW_UNKNOWN_MODE,
        view_pos = [],
        is_closed = None,
        n_kids = 0,
    )
    _compare_bookmark(
        next(toc),
        title = "A Good Ending",
        page_index = None,
        view_mode = pdfium_c.PDFDEST_VIEW_UNKNOWN_MODE,
        view_pos = [],
        is_closed = None,
        n_kids = 0,
    )
    with caplog.at_level(logging.WARNING):
        for other in toc: pass
    assert "circular bookmark reference" in caplog.text
