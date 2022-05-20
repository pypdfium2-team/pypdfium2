# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
from ..conftest import TestFiles
import pypdfium2 as pdfium


def test_pageobjects():
    doc = pdfium.PdfDocument(TestFiles.images)
    page = doc.get_page(0)
    
    pageobjs = pdfium.get_pageobjs(page)
    images = [img for img in pdfium.filter_pageobjs(pageobjs, pdfium.FPDF_PAGEOBJ_IMAGE)]
    assert len(images) == 3
    
    positions = [pdfium.locate_pageobj(img) for img in images]
    exp_positions = [
        [133, 459, 350, 550],
        [48, 652, 163, 700],
        [204, 204, 577, 360],
    ]
    assert len(positions) == len(exp_positions)
    for pos, exp_pos in zip(positions, exp_positions):
        assert pytest.approx(pos, abs=1) == exp_pos
    
    pdfium.close_page(page)
    doc.close()
