# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import re
import pytest
from os.path import join
from importlib.util import find_spec
import pypdfium2 as pdfium
from ..conftest import TestFiles, ResourceDir, OutputDir


@pytest.fixture
def doc():
    doc = pdfium.PdfDocument(TestFiles.text)
    yield doc
    # doc.close()


@pytest.fixture
def textpage(doc):
    page = doc.get_page(0)
    textpage = page.get_textpage()
    assert isinstance(textpage, pdfium.PdfTextPage)
    yield textpage
    # for g in (textpage, page): g.close()


@pytest.fixture
def linkpage(doc):
    page = doc.get_page(1)
    linkpage = page.get_textpage()
    yield linkpage
    # for g in (linkpage, page): g.close()


def test_gettext(textpage):
    text_a = textpage.get_text()
    text_b = textpage.get_text_range()
    assert text_a == text_b
    assert len(text_a) == 438
    exp_start = "Lorem ipsum dolor sit amet,\r\n"
    exp_end = "\r\nofficia deserunt mollit anim id est laborum."
    assert text_a.startswith(exp_start)
    assert text_a.endswith(exp_end)
    text_start = textpage.get_text_range(0, len(exp_start))
    text_end_a = textpage.get_text_range(len(text_a)-len(exp_end), 0)
    text_end_b = textpage.get_text_range(len(text_a)-len(exp_end), len(exp_end))
    assert text_start == exp_start
    assert text_end_a == text_end_b == exp_end


@pytest.mark.parametrize("loose", [False, True])
def test_getcharbox(textpage, loose):
    for index in range(textpage.n_chars):
        box = textpage.get_charbox(index, loose=loose)
        assert all( isinstance(val, (int, float)) for val in box )
        assert box[0] <= box[2] and box[1] <= box[3]


def test_getrectboxes(textpage):
    rects = textpage.get_rectboxes()
    
    first_rect = next(rects)
    assert pytest.approx(first_rect, abs=1) == (58, 767, 258, 782)
    first_text = textpage.get_text(*first_rect)
    assert first_text == "Lorem ipsum dolor sit amet,"
    assert textpage.get_text_range(0, len(first_text)) == first_text
    
    i = 0
    for rect in rects:
        assert len(rect) == 4
        assert 56 < rect[0] < 59
        text = textpage.get_text(*rect)
        assert isinstance(text, str)
        assert len(text) <= 66
        i += 1
    
    assert i == 9
    assert text == "officia deserunt mollit anim id est laborum."
    assert textpage.get_text_range(textpage.n_chars-len(text), 0)


def test_gettext_area_oob(textpage):
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
        with pytest.raises(ValueError, match=re.escape("Invalid page area requested.")):
            textpage.get_text(*area)


def test_search_text(textpage):
    searcher = textpage.search("labor")
    
    occ_1a = searcher.get_next()
    occ_2a = searcher.get_next()
    occ_3a = searcher.get_next()
    occ_4x = searcher.get_next()
    occ_2b = searcher.get_prev()
    occ_1b = searcher.get_prev()
    
    assert pytest.approx(occ_1a[0], abs=1) == (292, 678, 329, 690)
    assert pytest.approx(occ_2a[0], abs=1) == (324, 641, 360, 653)
    assert pytest.approx(occ_3a[0], abs=1) == (305, 549, 341, 561)
    assert occ_4x is None
    assert occ_1a == occ_1b and occ_2a == occ_2b
    
    for occ in (occ_1a, occ_2a, occ_3a):
        for box in occ:
            assert all(isinstance(val, (int, float)) for val in box)
            assert len(box) == 4
            assert box[0] <= box[2]
            assert box[1] <= box[3]
    
    # searcher.close()


def test_get_index(textpage):
    
    x, y = (60, textpage.page.get_height()-66)
    
    index = textpage.get_index(x, y, 5, 5)
    assert index < textpage.n_chars and index == 0
    
    charbox = textpage.get_charbox(index)
    char = textpage.get_text(*charbox)
    assert char == "L"


def test_textpage_empty():
    pdf = pdfium.PdfDocument(TestFiles.empty)
    page = pdf.get_page(0)
    textpage = page.get_textpage()
    
    assert textpage.get_text() == ""
    assert textpage.get_text_range() == ""
    assert textpage.n_chars == textpage.count_chars() == 0
    assert textpage.count_rects() == 0
    assert textpage.get_index(0, 0, 0, 0) is None
    assert [r for r in textpage.get_rectboxes()] == []
    
    searcher = textpage.search("a")
    assert searcher.get_next() is None
    # searcher.close()
    
    with pytest.raises(ValueError, match=re.escape("Character index 0 is out of bounds. The maximum index is -1.")):
        textpage.get_charbox(0)
    with pytest.raises(ValueError, match=re.escape("Text length must be >0.")):
        textpage.search("")
    
    # for g in (textpage, page, pdf): g.close()


def test_get_links(linkpage):
    exp_links = (
        "https://www.wikipedia.org/",
        "https://www.openstreetmap.org/",
        "https://www.opensuse.org/",
        "https://kde.org/",
    )
    for i, link in enumerate(linkpage.get_links()):
        assert link == exp_links[i]


@pytest.mark.skipif(not find_spec("uharfbuzz"), reason="uharfbuzz is not installed")
def test_insert_text():
    
    pdf = pdfium.PdfDocument.new()
    width, height = 500, 300
    page = pdf.new_page(width, height)
    assert page.get_size() == (width, height)
    
    NotoSans = join(ResourceDir, "NotoSans-Regular.ttf")
    hb_font = pdfium.HarfbuzzFont(NotoSans)
    pdf_font = pdf.add_font(
        NotoSans,
        type = pdfium.FPDF_FONT_TRUETYPE,
        is_cid = True,
    )
    
    message_a = "मैं घोषणा, पुष्टि और सहमत हूँ कि:"
    posx_a = 50
    posy_a = height - 75
    fs_a = 25
    
    message_b = "Latin letters test."
    posx_b = 50
    posy_b = height - 150
    fs_b = 30
    
    page.insert_text(
        text = message_a,
        pos_x = posx_a,
        pos_y = posy_a,
        font_size = fs_a,
        hb_font = hb_font,
        pdf_font = pdf_font,
    )
    page.insert_text(
        text = message_b,
        pos_x = posx_b,
        pos_y = posy_b,
        font_size = fs_b,
        hb_font = hb_font,
        pdf_font = pdf_font,
    )
    page.generate_content()
    
    textpage = page.get_textpage()
    assert textpage.get_text(left=posx_b, bottom=posy_b, top=posy_b+fs_b) == message_b
    # extraction of message_a xfails - it looks like no PDF software can reconstruct this text correctly
    # assert textpage.get_text(left=posx_a, bottom=posy_a, top=posy_a+fs_a) == "मၝघोषणाᆸपुჹ\u10cbऔर सहमत ီ\r\nँჸकᇆ"
    
    with open(join(OutputDir, "text_insertion.pdf"), "wb") as buffer:
        pdf.save(buffer, version=17)
    
    # for g in (textpage, page, pdf_font, pdf): g.close()
