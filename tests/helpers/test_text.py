# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import re
import pytest
import pypdfium2 as pdfium
from ..conftest import TestFiles


@pytest.fixture
def text_pdf():
    pdf = pdfium.PdfDocument(TestFiles.text)
    yield pdf


@pytest.fixture
def textpage(text_pdf):
    page = text_pdf.get_page(0)
    textpage = page.get_textpage()
    assert isinstance(textpage, pdfium.PdfTextPage)
    yield textpage


@pytest.fixture
def linkpage(text_pdf):
    page = text_pdf.get_page(1)
    linkpage = page.get_textpage()
    yield linkpage


def test_gettext(textpage):
    text_a = textpage.get_text_bounded()
    text_b = textpage.get_text_range()
    assert text_a == text_b
    assert len(text_a) == 438
    exp_start = "Lorem ipsum dolor sit amet,\r\n"
    exp_end = "\r\nofficia deserunt mollit anim id est laborum."
    assert text_a.startswith(exp_start)
    assert text_a.endswith(exp_end)
    text_start = textpage.get_text_range(0, len(exp_start))
    text_end_a = textpage.get_text_range(len(text_a)-len(exp_end))  # count=-1
    text_end_b = textpage.get_text_range(len(text_a)-len(exp_end), len(exp_end))
    assert text_start == exp_start
    assert text_end_a == text_end_b == exp_end


@pytest.mark.parametrize("loose", [False, True])
def test_getcharbox(textpage, loose):
    for index in range(textpage.count_chars()):
        box = textpage.get_charbox(index, loose=loose)
        assert all( isinstance(val, (int, float)) for val in box )
        assert box[0] <= box[2] and box[1] <= box[3]


def test_getrectboxes(textpage):
    n_rects = textpage.count_rects()
    rects = [textpage.get_rect(i) for i in range(n_rects)]
    assert len(rects) == 10
    
    first_rect = rects[0]
    assert pytest.approx(first_rect, abs=1) == (58, 767, 258, 782)
    first_text = textpage.get_text_bounded(*first_rect)
    assert first_text == "Lorem ipsum dolor sit amet,"
    assert textpage.get_text_range(0, len(first_text)) == first_text
    
    for rect in rects:
        assert len(rect) == 4
        assert 56 < rect[0] < 59
        text = textpage.get_text_bounded(*rect)
        assert isinstance(text, str)
        assert len(text) <= 66
    
    assert text == "officia deserunt mollit anim id est laborum."
    assert textpage.get_text_range(textpage.count_chars()-len(text))  # count=-1


def _get_rects(textpage, search_result):
    # TODO add helper?
    if search_result is None:
        return
    c_index, c_count = search_result
    r_index = textpage.count_rects(0, c_index)
    r_count = textpage.count_rects(c_index, c_count)
    rects = [textpage.get_rect(i) for i in range(r_index, r_index+r_count)]
    return rects


def test_search_text(textpage):
    searcher = textpage.search("labor")
    
    occ_1a = searcher.get_next()
    occ_2a = searcher.get_next()
    occ_3a = searcher.get_next()
    occ_4x = searcher.get_next()
    occ_2b = searcher.get_prev()
    occ_1b = searcher.get_prev()
    
    assert occ_1a == (89, 5)
    assert occ_2a == (181, 5)
    assert occ_3a == (430, 5)
    assert occ_4x is None
    assert occ_1a == occ_1b and occ_2a == occ_2b
    
    _get_rects(textpage, occ_1a) == [ (292, 678, 329, 690) ]
    _get_rects(textpage, occ_2a) == [ (324, 641, 360, 653) ]
    _get_rects(textpage, occ_3a) == [ (305, 549, 341, 561) ]


def test_get_index(textpage):
    
    x, y = (60, textpage.page.get_height()-66)
    
    index = textpage.get_index(x, y, 5, 5)
    assert index < textpage.count_chars() and index == 0
    
    charbox = textpage.get_charbox(index)
    char = textpage.get_text_bounded(*charbox)
    assert char == "L"


def test_textpage_empty():
    pdf = pdfium.PdfDocument(TestFiles.empty)
    page = pdf.get_page(0)
    textpage = page.get_textpage()
    
    assert textpage.get_text_bounded() == ""
    assert textpage.get_text_range() == ""
    assert textpage.count_chars() == 0
    assert textpage.count_rects() == 0
    assert textpage.get_index(0, 0, 0, 0) is None
    
    searcher = textpage.search("a")
    assert searcher.get_next() is None
    
    with pytest.raises(pdfium.PdfiumError, match=re.escape("Failed to get charbox.")):
        textpage.get_charbox(0)
    with pytest.raises(ValueError, match=re.escape("Text length must be greater than 0.")):
        textpage.search("")
