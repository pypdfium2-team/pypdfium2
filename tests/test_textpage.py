# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2 as pdfium
from .conftest import TestResources


def test_get_text_bounded_defaults_with_rotation():
    
    # Regression test for BUG(149):
    # Make sure defaults use native PDF coordinates instead of normalized page size
    
    pdf = pdfium.PdfDocument(TestResources.text)
    page = pdf.get_page(0)
    page.set_rotation(90)
    textpage = page.get_textpage()
    
    text = textpage.get_text_bounded()
    assert len(text) == 438
