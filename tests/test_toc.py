# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
import logging
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_r
from .conftest import TestResources


def _compare_bookmark(bookmark, exp_title, exp_count, exp_index=None, exp_view=None):
    
    assert exp_title == bookmark.get_title()
    assert exp_count == bookmark.get_count()
    
    dest = bookmark.get_dest()
    if dest is None:
        assert all(exp is None for exp in (exp_index, exp_view))
    else:
        assert dest.get_index() == exp_index
        exp_mode, exp_pos = exp_view
        mode, pos = dest.get_view()
        assert exp_mode == mode
        assert pytest.approx(pos, abs=1) == exp_pos


def test_gettoc():
    
    pdf = pdfium.PdfDocument(TestResources.toc)
    toc = pdf.get_toc()
    
    # check first bookmark
    _compare_bookmark(
        next(toc),
        exp_title = "One",
        exp_count = -2,
        exp_index = 0,
        exp_view = (pdfium_r.PDFDEST_VIEW_XYZ, (89, 758, 0)),
    )
    
    # check common values
    for bookmark in toc:
        dest = bookmark.get_dest()
        view_mode, view_pos = dest.get_view()
        assert view_mode == pdfium_r.PDFDEST_VIEW_XYZ
        assert round(view_pos[0]) == 89
    
    # check last bookmark
    _compare_bookmark(
        bookmark,
        exp_title = "Three-B",
        exp_count = 0,
        exp_index = 1,
        exp_view = (pdfium_r.PDFDEST_VIEW_XYZ, (89, 657, 0)),
    )


def test_gettoc_circular(caplog):
    
    pdf = pdfium.PdfDocument(TestResources.toc_circular)
    toc = pdf.get_toc()
    
    _compare_bookmark(
        next(toc),
        exp_title = "A Good Beginning",
        exp_count = 0,
    )
    _compare_bookmark(
        next(toc),
        exp_title = "A Good Ending",
        exp_count = 0,
    )
    with caplog.at_level(logging.WARNING):
        for other in toc: pass
    assert "circular bookmark reference" in caplog.text
