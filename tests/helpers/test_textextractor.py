# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
from ..conftest import TestFiles
import pypdfium2 as pdfium


@pytest.fixture
def doc():
    doc = pdfium.PdfDocument(TestFiles.text)
    yield doc
    doc.close()

@pytest.fixture
def page(doc):
    page = doc.get_page(0)
    yield page
    pdfium.close_page(page)

@pytest.fixture
def textpage(page):
    textpage = pdfium.PdfTextPage(page)
    yield textpage
    textpage.close()


def test_gettext_page(textpage):
    text = textpage.get_text()
    print(text)
    assert len(text) == 438
    assert text.startswith("Lorem ipsum dolor sit amet,\r\n")
    assert text.endswith("\r\nofficia deserunt mollit anim id est laborum.")


@pytest.mark.parametrize("loose", [False, True])
def test_getcharbox(textpage, loose):
    for index in range( textpage.count_chars() ):
        box = textpage.get_charbox(index, loose=loose)
        assert all( isinstance(val, (int, float)) for val in box )
        assert box[0] <= box[2] and box[1] <= box[3]


def test_getrectboxes(textpage):
    rects = textpage.get_rectboxes()
    
    first_rect = next(rects)
    assert pytest.approx(first_rect, abs=1) == [58, 767, 258, 782]
    first_text = textpage.get_text(*first_rect)
    assert first_text == "Lorem ipsum dolor sit amet,"
    print(first_rect, first_text)
    
    i = 0
    for rect in rects:
        assert len(rect) == 4
        assert 56 < rect[0] < 59
        text = textpage.get_text(*rect)
        print(rect, text)
        assert isinstance(text, str)
        assert len(text) <= 66
        i += 1
    
    assert i == 9
    assert text == "officia deserunt mollit anim id est laborum."


def test_textpage_empty():
    doc = pdfium.PdfDocument(TestFiles.empty)
    textpage = doc.get_textpage(0)
    
    assert textpage.get_text() == ""
    assert textpage.count_chars() == 0
    assert textpage.count_rects() == 0
    assert textpage.get_index(0, 0, 0, 0) is None
    assert [r for r in textpage.get_rectboxes()] == []
    
    searcher = textpage.search("a")
    assert searcher.get_next() is None
    searcher.close()
    
    with pytest.raises(ValueError, match="Character index 0 is out of bounds. The maximum index is -1."):
        textpage.get_charbox(0)
    with pytest.raises(ValueError, match="Text length must be >0."):
        textpage.search("")
    
    textpage.close()
    doc.close()


def test_area_oob(textpage):
    areas = [
        (-1, 0, 0, 0),   # left too low
        (0, -1, 0, 0),   # bottom too low
        (0, 0, -1, 0),   # right too low
        (0, 0, 0, -1),   # top too low
        (600, 0, 0, 0),  # left too high
        (0, 900, 0, 0),  # bottom too high
        (0, 0, 600, 0),  # right too high
        (0, 0, 0, 900),  # top too high
        (100, 0, 50, 0), # left higher than right
        (0, 100, 0, 50), # bottom higher than top
    ]
    for area in areas:
        with pytest.raises(ValueError, match="Invalid page area requested."):
            textpage.get_text(*area)


def test_search_text(textpage):
    searcher = textpage.search("labor")
    assert isinstance(searcher, pdfium.TextSearcher)
    
    occ_1a = searcher.get_next()
    occ_2a = searcher.get_next()
    occ_3a = searcher.get_next()
    
    occ_4a = searcher.get_next()
    
    occ_2b = searcher.get_prev()
    occ_1b = searcher.get_prev()
    
    for occ in (occ_1a, occ_2a, occ_3a):
        for box in occ:
            assert all(isinstance(val, (int, float)) for val in box)
            assert len(box) == 4
            assert box[0] <= box[2]
            assert box[1] <= box[3]
    
    assert occ_1a == occ_1b and occ_2a == occ_2b
    assert occ_4a is None
    
    searcher.close()


def test_get_index(page, textpage):
    
    height = pdfium.FPDF_GetPageHeightF(page)
    x, y = (60, height-66)
    
    n_chars = textpage.count_chars()
    index = textpage.get_index(x, y, 5, 5)
    assert index < n_chars and index == 0
    
    charbox = textpage.get_charbox(index)
    char = textpage.get_text(*charbox)
    assert char == "L"
