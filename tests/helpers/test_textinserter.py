# SPDX-FileCopyrightText: 2022 Anurag Bansal <anurag.bansal.585@gmail.com>
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from os.path import join
from importlib.util import find_spec
import pytest
import pypdfium2 as pdfium
from ..conftest import ResourceDir, OutputDir


@pytest.mark.skipif(not find_spec("uharfbuzz"), reason="uharfbuzz is not installed")
def test_insert_text():
    
    pdf = pdfium.FPDF_CreateNewDocument()
    pdfium.FPDFPage_New(pdf, 0, 500, 800)
    
    NotoSans = join(ResourceDir, "NotoSans-Regular.ttf")
    font_info = pdfium.FontInfo(NotoSans)
    pdf_font = pdfium.open_pdffont(
        pdf, NotoSans,
        type = pdfium.FPDF_FONT_TRUETYPE,
        is_cid = True,
    )
    
    pdfium.insert_text(
        pdf, 0,
        text = "मैं घोषणा, पुष्टि और सहमत हूँ कि:",
        pos_x = 100,
        pos_y = 700,
        font_size = 25,
        font_info = font_info,
        pdf_font = pdf_font,
    )
    pdfium.insert_text(
        pdf, 0,
        text = "Latin letters test.",
        pos_x = 100,
        pos_y = 600,
        font_size = 30,
        font_info = font_info,
        pdf_font = pdf_font,
    )
    
    pdfium.close_pdffont(pdf_font)
    
    with open(join(OutputDir, "text_insertion.pdf"), "wb") as buffer:
        pdfium.save_pdf(pdf, buffer, version=17)
