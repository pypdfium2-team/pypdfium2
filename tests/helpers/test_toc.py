# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import pytest
import logging
import contextlib
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c
from ..conftest import TestFiles


@pytest.fixture
def toc_doc():
    doc = pdfium.PdfDocument(TestFiles.toc)
    yield doc

@pytest.fixture
def toc_circular_doc():
    doc = pdfium.PdfDocument(TestFiles.toc_circular)
    yield doc


def _compare_bookmark(bookmark, **kwargs):
    for name, exp_value in kwargs.items():
        value = getattr(bookmark, name)
        if name == "view_pos":
            assert pytest.approx(value, abs=1) == exp_value
        else:
            assert value == exp_value


def test_gettoc(toc_doc):
    
    toc = toc_doc.get_toc()
    
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


def test_gettoc_circular(toc_circular_doc, caplog):
    toc = toc_circular_doc.get_toc()
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
    
    maxdepth_doc = pdfium.PdfDocument(TestFiles.toc_maxdepth)
    _test_printtoc(maxdepth_doc, TocResult_D, max_depth=10)


TocResult_A = """\
[-] One -> 1  # XYZ [89.29, 757.7, 0.0]
    [*] One-A -> 1  # XYZ [89.29, 706.86, 0.0]
    [-] One-B -> 1  # XYZ [89.29, 657.03, 0.0]
        [*] One-B-I -> 1  # XYZ [89.29, 607.2, 0.0]
        [*] One-B-II -> 1  # XYZ [89.29, 557.76, 0.0]
[*] Two -> 1  # XYZ [89.29, 507.16, 0.0]
[-] Three -> 2  # XYZ [89.29, 757.7, 0.0]
    [*] Three-A -> 2  # XYZ [89.29, 706.98, 0.0]
    [*] Three-B -> 2  # XYZ [89.29, 657.15, 0.0]
"""

TocResult_B = """\
[*] A Good Beginning -> ?  # ? []
[*] A Good Ending -> ?  # ? []
"""

TocResult_C = """\
[*] XYZ 2.1-Page1 red bold -> 1  # XYZ [100.0, 100.0, 2.1]
[*] Fit-Page2 green Italic -> 2  # Fit []
[*] FitB Italic&Bold b -> 3  # FitB []
[*] FitV Page4 -> 4  # FitV [500.0]
[*] FitH Page5 -> 5  # FitH [600.0]
[*] FitR Page6 -> 6  # FitR [100.0, 100.0, 200.0, 200.0]
[*] FitBH Page7 -> 7  # FitBH [100.0]
[*] FitBV Page8 -> 8  # FitBV [100.0]
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
            [*] 2.1.1.1.outline -> 2  # FitH [583.18]
    [*] 2.2 outline -> 2  # FitH [515.22]
"""
