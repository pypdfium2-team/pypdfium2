# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import pytest
import logging
import contextlib
import pypdfium2 as pdfium
from ..conftest import TestFiles


@pytest.fixture
def toc_doc():
    doc = pdfium.PdfDocument(TestFiles.toc)
    yield doc
    doc.close()

@pytest.fixture
def toc_circular_doc():
    doc = pdfium.PdfDocument(TestFiles.toc_circular)
    yield doc
    doc.close()


def _compare_bookmark(bookmark, title, page_index, view_mode, view_pos, is_closed):
    assert bookmark.title == title
    assert bookmark.page_index == page_index
    assert bookmark.view_mode == view_mode
    assert pytest.approx(bookmark.view_pos, abs=1) == view_pos
    assert bookmark.is_closed == is_closed


def test_gettoc(toc_doc):
    
    toc = toc_doc.get_toc()
    
    # check first bookmark
    _compare_bookmark(
        next(toc),
        title = "One",
        page_index = 0,
        view_mode = pdfium.PDFDEST_VIEW_XYZ,
        view_pos = (89, 758, 0),
        is_closed = True,
    )
    
    # check common values
    for bookmark in toc:
        assert isinstance(bookmark, pdfium.OutlineItem)
        assert bookmark.view_mode is pdfium.PDFDEST_VIEW_XYZ
        assert round(bookmark.view_pos[0]) == 89
    
    # check last bookmark
    _compare_bookmark(
        bookmark,
        title = "Three-B",
        page_index = 1,
        view_mode = pdfium.PDFDEST_VIEW_XYZ,
        view_pos = (89, 657, 0),
        is_closed = False,
    )


def test_gettoc_circular(toc_circular_doc, caplog):
    toc = toc_circular_doc.get_toc()
    _compare_bookmark(
        next(toc),
        title = "A Good Beginning",
        page_index = -1,
        view_mode = pdfium.PDFDEST_VIEW_UNKNOWN_MODE,
        view_pos = [],
        is_closed = False,
    )
    _compare_bookmark(
        next(toc),
        title = "A Good Ending",
        page_index = -1,
        view_mode = pdfium.PDFDEST_VIEW_UNKNOWN_MODE,
        view_pos = [],
        is_closed = False,
    )
    with caplog.at_level(logging.WARNING):
        for other in toc: pass
    assert "circular bookmark reference" in caplog.text


def _test_printtoc(doc, exp_result, max_depth=15):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        doc.print_toc( doc.get_toc(max_depth=max_depth) )
    assert buffer.getvalue() == exp_result


def test_toc_misc(toc_doc, toc_circular_doc):
    
    _test_printtoc(toc_doc, TocResult_A)
    _test_printtoc(toc_circular_doc, TocResult_B)
    
    viewmodes_doc = pdfium.PdfDocument(TestFiles.toc_viewmodes)
    _test_printtoc(viewmodes_doc, TocResult_C)
    viewmodes_doc.close()
    
    maxdepth_doc = pdfium.PdfDocument(TestFiles.toc_maxdepth)
    _test_printtoc(maxdepth_doc, TocResult_D, max_depth=10)
    maxdepth_doc.close()


TocResult_A = """\
[-] One -> 1  # XYZ [89.29, 757.7, 0.0]
    [+] One-A -> 1  # XYZ [89.29, 706.86, 0.0]
    [-] One-B -> 1  # XYZ [89.29, 657.03, 0.0]
        [+] One-B-I -> 1  # XYZ [89.29, 607.2, 0.0]
        [+] One-B-II -> 1  # XYZ [89.29, 557.76, 0.0]
[+] Two -> 1  # XYZ [89.29, 507.16, 0.0]
[-] Three -> 2  # XYZ [89.29, 757.7, 0.0]
    [+] Three-A -> 2  # XYZ [89.29, 706.98, 0.0]
    [+] Three-B -> 2  # XYZ [89.29, 657.15, 0.0]
"""

TocResult_B = """\
[+] A Good Beginning -> 0  # Unknown []
[+] A Good Ending -> 0  # Unknown []
"""

TocResult_C = """\
[+] XYZ 2.1-Page1 red bold -> 1  # XYZ [100.0, 100.0, 2.1]
[+] Fit-Page2 green Italic -> 2  # Fit []
[+] FitB Italic&Bold b -> 3  # FitB []
[+] FitV Page4 -> 4  # FitV [500.0]
[+] FitH Page5 -> 5  # FitH [600.0]
[+] FitR Page6 -> 6  # FitR [100.0, 100.0, 200.0, 200.0]
[+] FitBH Page7 -> 7  # FitBH [100.0]
[+] FitBV Page8 -> 8  # FitBV [100.0]
"""

TocResult_D = """\
[+] 1.outline -> 1  # FitH [746.44]
    [+] 1.1.outline -> 1  # FitH [700.88]
        [+] 1.1.1.outline -> 1  # FitH [632.54]
            [+] 1.1.1.1.outline -> 1  # FitH [632.95]
                [+] 1.1.1.1.1.outline -> 1  # FitH [597.3]
                    [+] 1.1.1.1.1.1outline -> 1  # FitH [632.95]
                        [+] 1.1.1.1.1.1.outline -> 1  # FitH [632.95]
                            [+] 1.1.1.1.1.1.1.outline -> 1  # FitH [632.95]
                                [+] 1.1.1.1.1.1.1.1.outline -> 1  # FitH [632.95]
                                    [+] 1.1.1.1.1.1.1.1.1.outline -> 1  # FitH [632.95]
[+] 2.outline -> 2  # FitH [749.48]
    [+] 2.1.outline -> 2  # FitH [699.36]
        [+] 2.1.1.outline -> 2  # FitH [628.74]
            [+] 2.1.1.1.outline -> 2  # FitH [583.18]
    [+] 2.2 outline -> 2  # FitH [515.22]
"""
