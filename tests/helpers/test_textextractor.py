# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
from ..conftest import TestFiles
import pypdfium2 as pdfium


@pytest.fixture
def textpage():
    doc = pdfium.PdfDocument(TestFiles.text)
    textpage = doc.get_textpage(0)
    yield textpage
    textpage.close()
    doc.close()


def test_gettext_page(textpage):
    text = textpage.get_text()
    print(text)
    assert len(text) == 438
    assert text.startswith("Lorem ipsum dolor sit amet,\r\n")
    assert text.endswith("\r\nofficia deserunt mollit anim id est laborum.")


def test_getrects(textpage):
    rects = textpage.get_rects()
    
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
    assert [r for r in textpage.get_rects()] == []
    
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
