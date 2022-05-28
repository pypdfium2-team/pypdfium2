# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
import pypdfium2 as pdfium
from ..conftest import TestFiles


def test_boxes():
    
    pdf = pdfium.PdfDocument(TestFiles.render)
    page = pdf.get_page(0)
    assert page.get_size() == (595, 842)
    assert page.get_mediabox() == (0, 0, 595, 842)
    assert isinstance(page, pdfium.PdfPage)
    
    test_cases = [
        ("media", (0,  0,  612, 792)),
        ("media", (0,  0,  595, 842)),
        ("crop",  (10, 10, 585, 832)),
        ("bleed", (20, 20, 575, 822)),
        ("trim",  (30, 30, 565, 812)),
        ("art",   (40, 40, 555, 802)),
    ]
    
    for meth_name, exp_box in test_cases:
        getattr(page, "set_%sbox" % meth_name)(*exp_box)
        box = getattr(page, "get_%sbox" % meth_name)()
        assert pytest.approx(box) == exp_box
    
    [g.close() for g in (page, pdf)]


def test_mediabox_fallback():
    pdf = pdfium.PdfDocument(TestFiles.box_fallback)
    page = pdf.get_page(0)
    assert page.get_mediabox() == (0, 0, 612, 792)
    [g.close() for g in (page, pdf)]


def test_rotation():
    pdf = pdfium.PdfDocument.new()
    page = pdf.new_page(500, 800)
    for r in (90, 180, 270, 0):
        page.set_rotation(r)
        assert page.get_rotation() == r
    [g.close() for g in (page, pdf)]


def test_pageobjects():
    pdf = pdfium.PdfDocument(TestFiles.images)
    page = pdf.get_page(0)
    
    images = [obj for obj in page.get_objects() if obj.get_type() == pdfium.FPDF_PAGEOBJ_IMAGE]
    assert len(images) == 3
    
    positions = [img.get_pos() for img in images]
    exp_positions = [
        (133, 459, 350, 550),
        (48, 652, 163, 700),
        (204, 204, 577, 360),
    ]
    assert len(positions) == len(exp_positions)
    for pos, exp_pos in zip(positions, exp_positions):
        assert pytest.approx(pos, abs=1) == exp_pos
    
    [g.close() for g in (page, pdf)]
