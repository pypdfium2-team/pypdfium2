# SPDX-FileCopyrightText: 2022 Anurag Bansal <anurag.bansal.585@gmail.com>
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
from os.path import join
import pypdfium2 as pdfium
import pytest
from ..conftest import ResourceDir, OutputDir


NotoSans = join(ResourceDir, "NotoSans-Regular.ttf")

def test_insert_hindi():
    
    pdf = pdfium.FPDF_CreateNewDocument()
    pdfium.FPDFPage_New(pdf, 0, 500, 800)
    
    pdfium.insert_text(
        pdf, 0,
        text = "मैं घोषणा, पुष्टि और सहमत हूँ कि:",
        pos_x = 100,
        pos_y = 700,
        font_path = NotoSans,
        font_size = 25,
        font_type = pdfium.FPDF_FONT_TRUETYPE,
        font_is_cid = True,
    )
    
    with open(join(OutputDir, "text_hindi.pdf"), "wb") as buffer:
        pdfium.save_pdf(pdf, buffer, version=17)
