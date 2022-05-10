# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2 as pdfium
from pytest import approx
from ..conftest import TestFiles


def test_boxes():
    
    with pdfium.PdfContext(TestFiles.boxes) as pdf:
        
        page_a = pdfium.open_page(pdf, 0)
        page_b = pdfium.open_page(pdf, 1)
        
        test_cases = [
            (page_a, pdfium.get_mediabox, (0,  0,  612, 792)),
            (page_b, pdfium.get_mediabox, (0,  0,  595, 842)),
            (page_b, pdfium.get_cropbox,  (10, 10, 585, 832)),
            (page_b, pdfium.get_bleedbox, (20, 20, 575, 822)),
            (page_b, pdfium.get_trimbox,  (30, 30, 565, 812)),
            (page_b, pdfium.get_artbox,   (40, 40, 555, 802)),
        ]
        
        for page, box_func, exp_box in test_cases:
            assert approx( box_func(page) ) == exp_box
        
        for page in (page_a, page_b):
            pdfium.FPDF_ClosePage(page)
