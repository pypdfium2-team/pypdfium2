#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-FileCopyrightText: 2020 Yinlin Hu <huyinlin@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0

import sys
import math
import ctypes
from PIL import Image
import pypdfium2 as pdfium


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: example.py somefile.pdf")
        sys.exit()
    
    filename = sys.argv[1]
    
    doc = pdfium.FPDF_LoadDocument(filename, None)
    page_count = pdfium.FPDF_GetPageCount(doc)
    assert page_count >= 1
    
    form_config = pdfium.FPDF_FORMFILLINFO(2)
    form_fill = pdfium.FPDFDOC_InitFormFillEnvironment(doc, form_config)
    
    page = pdfium.FPDF_LoadPage(doc, 0)
    width = math.ceil(pdfium.FPDF_GetPageWidthF(page))
    height = math.ceil(pdfium.FPDF_GetPageHeightF(page))
    
    bitmap = pdfium.FPDFBitmap_Create(width, height, 0)
    pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, 0xFFFFFFFF)
    
    render_args = [bitmap, page, 0, 0, width, height, 0,  pdfium.FPDF_LCD_TEXT | pdfium.FPDF_ANNOT]
    pdfium.FPDF_RenderPageBitmap(*render_args)
    pdfium.FPDF_FFLDraw(form_fill, *render_args)
    
    cbuffer = pdfium.FPDFBitmap_GetBuffer(bitmap)
    buffer = ctypes.cast(cbuffer, ctypes.POINTER(ctypes.c_ubyte * (width * height * 4)))
    
    img = Image.frombuffer("RGBA", (width, height), buffer.contents, "raw", "BGRA", 0, 1)
    img.save("out.png")
    
    pdfium.FPDFBitmap_Destroy(bitmap)
    pdfium.FPDF_ClosePage(page)
    
    pdfium.FPDFDOC_ExitFormFillEnvironment(form_fill)
    pdfium.FPDF_CloseDocument(doc)
