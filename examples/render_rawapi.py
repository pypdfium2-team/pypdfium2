#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
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

    doc = pdfium.FPDF_LoadDocument(filename, None) # load document (filename, password string)
    page_count = pdfium.FPDF_GetPageCount(doc)     # get page count
    assert page_count >= 1

    page   = pdfium.FPDF_LoadPage(doc, 0)                # load the first page
    width  = math.ceil(pdfium.FPDF_GetPageWidthF(page))  # get page width
    height = math.ceil(pdfium.FPDF_GetPageHeightF(page)) # get page height

    # render to bitmap
    bitmap = pdfium.FPDFBitmap_Create(width, height, 0)
    pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, 0xFFFFFFFF)
    pdfium.FPDF_RenderPageBitmap(
        bitmap, page, 0, 0, width, height, 0, 
        pdfium.FPDF_LCD_TEXT | pdfium.FPDF_ANNOT
    )

    # retrieve data from bitmap
    cbuffer = pdfium.FPDFBitmap_GetBuffer(bitmap)
    buffer = ctypes.cast(cbuffer, ctypes.POINTER(ctypes.c_ubyte * (width * height * 4)))

    img = Image.frombuffer("RGBA", (width, height), buffer.contents, "raw", "BGRA", 0, 1)
    img.save("out.png")

    pdfium.FPDFBitmap_Destroy(bitmap)
    pdfium.FPDF_ClosePage(page)

    pdfium.FPDF_CloseDocument(doc)
