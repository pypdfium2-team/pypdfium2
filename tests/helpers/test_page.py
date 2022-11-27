# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
import pypdfium2 as pdfium
# import pypdfium2.raw as pdfium_c
from ..conftest import TestFiles


def test_boxes():
    
    pdf = pdfium.PdfDocument(TestFiles.render)
    index = 0
    page = pdf.get_page(index)
    assert page.get_size() == pdf.get_page_size(index) == (595, 842)
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


def test_mediabox_fallback():
    pdf = pdfium.PdfDocument(TestFiles.box_fallback)
    page = pdf.get_page(0)
    assert page.get_mediabox() == (0, 0, 612, 792)


def test_rotation():
    pdf = pdfium.PdfDocument.new()
    page = pdf.new_page(500, 800)
    for r in (90, 180, 270, 0):
        page.set_rotation(r)
        assert page.get_rotation() == r


def test_page_labels():
    # incidentally, it happens that this TOC test file also has page labels
    pdf = pdfium.PdfDocument(TestFiles.toc_viewmodes)
    exp_labels = ["i", "ii", "appendix-C", "appendix-D", "appendix-E", "appendix-F", "appendix-G", "appendix-H"]
    assert exp_labels == [pdf.get_page_label(i) for i in range(len(pdf))]


# # disabled because flattening takes no effect
# def test_flatten():
    
#     pdf = pdfium.PdfDocument(TestFiles.form)
#     page = pdf[0]
    
#     rc = page._flatten()
#     assert rc == pdfium_c.FLATTEN_SUCCESS
    
#     # pdf.save(OutputDir / "flattened.pdf")
