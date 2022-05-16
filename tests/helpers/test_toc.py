# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import logging
from pytest import approx
import pypdfium2 as pdfium
from pypdfium2._cli.toc import print_toc
from ..conftest import TestFiles


def _compare_bookmark(bookmark, title, page_index, view_mode, view_pos, is_closed):
    assert bookmark.title == title
    assert bookmark.page_index == page_index
    assert bookmark.view_mode == view_mode
    assert approx(bookmark.view_pos, rel=0.01) == view_pos
    assert bookmark.is_closed == is_closed


def test_gettoc():
    
    doc = pdfium.PdfDocument(TestFiles.bookmarks)
    toc = doc.get_toc()
    
    # check first bookmark
    _compare_bookmark(
        next(toc),
        title = "One",
        page_index = 0,
        view_mode = pdfium.ViewMode.XYZ,
        view_pos = (89, 758, 0),
        is_closed = True,
    )
    
    # check common values
    for bookmark in toc:
        assert isinstance(bookmark, pdfium.OutlineItem)
        assert bookmark.view_mode is pdfium.ViewMode.XYZ
        assert round(bookmark.view_pos[0]) == 89
    
    # check last bookmark
    _compare_bookmark(
        bookmark,
        title = "Three-B",
        page_index = 1,
        view_mode = pdfium.ViewMode.XYZ,
        view_pos = (89, 657, 0),
        is_closed = False
    )
    
    doc.close()


def test_gettoc_circular(caplog):
    with caplog.at_level(logging.CRITICAL):
        with pdfium.PdfContext(TestFiles.bookmarks_circular) as pdf:
            toc = pdfium.get_toc(pdf)
            print_toc(toc)
            assert "circular bookmark reference" in caplog.text


def test_printtoc():
    with pdfium.PdfContext(TestFiles.bookmarks) as pdf:
        toc = pdfium.get_toc(pdf)
        print()
        print_toc(toc)


def test_gettoc_maxdepth():
    
    doc = pdfium.PdfDocument(TestFiles.bookmarks)
    toc = [b for b in doc.get_toc(max_depth=1)]
    assert len(toc) == 3
    print_toc(toc)
    
    doc.close()
