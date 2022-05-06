# SPDX-FileCopyrightText: 2022 Anurag Bansal <anurag.bansal.585@gmail.com>
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers.opener import open_page

try:
    import uharfbuzz as harfbuzz
except ImportError:
    have_harfbuzz = False
else:
    have_harfbuzz = True


def insert_text(
        pdf,
        page_index,
        text,
        pos_x,
        pos_y,
        font_path,
        font_size,
        font_type,
        font_is_cid,
    ):
    """
    Insert text into a PDF page at a specified position. This function supports Asian scripts such as hindi.
    There is no position validation, so make sure the text will be within page boundaries.
    ``uharfbuzz`` is required as an additional dependency.
    
    Parameters:
        pdf (``FPDF_DOCUMENT``):
            PDFium document handle.
        page_index (int):
            Zero-based index of the page to edit.
        text (str):
            The message to insert.
        pos_x (float):
            Distance from left border to first character.
        pos_y (float):
            Distance from bottom border to first character.
        font_path (str):
            File path of the font to use.
        font_size (float):
            Font size to use.
        font_type (int):
            State the type of the given font (``FPDF_FONT_TYPE1`` or ``FPDF_FONT_TRUETYPE``).
        font_is_cid (bool):
            State whether the given font is a CID font.
    """
    
    if not have_harfbuzz:
        raise RuntimeError("Function insert_text() requires uharfbuzz to be installed.")
    
    with open(font_path, "rb") as fh:
        font_data = fh.read()
    
    page = open_page(pdf, page_index)
    
    hb_blob = harfbuzz.Blob.from_file_path(font_path)
    hb_face = harfbuzz.Face(hb_blob)
    hb_font = harfbuzz.Font(hb_face)
    hb_fontscale = hb_font.scale[0]
    
    pdf_font = pdfium.FPDFText_LoadFont(
        pdf,
        ctypes.cast(font_data, ctypes.POINTER(ctypes.c_uint8)),
        len(font_data),
        font_type,
        font_is_cid,
    )
    
    hb_buffer = harfbuzz.Buffer()
    hb_buffer.add_str(text)
    hb_buffer.guess_segment_properties()
    hb_features = {"kern": True, "liga": True}
    harfbuzz.shape(hb_font, hb_buffer, hb_features)
    
    start_point = pos_x
    
    for info, pos in zip(hb_buffer.glyph_infos, hb_buffer.glyph_positions):
        
        pdf_textobj = pdfium.FPDFPageObj_CreateTextObj(pdf, pdf_font, font_size)
        pdfium.FPDFText_SetCharcodes(pdf_textobj, ctypes.c_uint32(info.codepoint), 1)
        pdfium.FPDFPageObj_Transform(
            pdf_textobj,
            1, 0, 0, 1,
            start_point - (pos.x_offset / hb_fontscale) * font_size,
            pos_y,
        )
        pdfium.FPDFPage_InsertObject(page, pdf_textobj)
        start_point += (pos.x_advance / hb_fontscale) * font_size
    
    pdfium.FPDFPage_GenerateContent(page)
