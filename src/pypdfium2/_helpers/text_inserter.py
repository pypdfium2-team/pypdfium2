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


class FontInfo:
    """
    Object to cache harfbuzz font data.
    
    Parameters:
        font_path (str):
            File path of the font to use.
    """
    
    def __init__(self, font_path):
        if not have_harfbuzz:
            raise RuntimeError("Font helpers require uharfbuzz to be installed.")
        self.hb_blob = harfbuzz.Blob.from_file_path(font_path)
        self.hb_face = harfbuzz.Face(self.hb_blob)
        self.hb_font = harfbuzz.Font(self.hb_face)
        self.hb_scale = self.hb_font.scale[0]


def open_pdffont(pdf, font_path, type, is_cid):
    """
    Create a PDFium font object handle. When you have finished working with the font, call :func:`.close_pdffont`.
    
    Parameters:
        pdf (``FPDF_DOCUMENT``):
            PDFium document handle.
        font_path (str):
            File path of the font to use.
        type (int):
            Type of the given font (``FPDF_FONT_TYPE1`` or ``FPDF_FONT_TRUETYPE``).
        is_cid (bool):
            :data:`True` if the font is a CID font, :data:`False` otherwise.
    Returns:
        ``FPDF_FONT``
    """
    with open(font_path, "rb") as fh:
        data = fh.read()
    return pdfium.FPDFText_LoadFont(
        pdf,
        ctypes.cast(data, ctypes.POINTER(ctypes.c_uint8)),
        len(data),
        type,
        is_cid,
    )


def close_pdffont(pdf_font):
    """
    Close a PDFium font object handle.
    
    Parameters:
        pdf_font (``FPDF_FONT``):
            The font object to close.
    """
    return pdfium.FPDFFont_Close(pdf_font)


def insert_text(
        pdf,
        page_index,
        text,
        pos_x,
        pos_y,
        font_size,
        font_info,
        pdf_font,
    ):
    """
    Insert text into a PDF page at a specified position using the writing system's ligature.
    This function supports Asian scripts such as Hindi. ``uharfbuzz`` is required as an additional dependency.
    
    Parameters:
        pdf (``FPDF_DOCUMENT``):
            PDFium document handle.
        page_index (int):
            Zero-based index of the page on which to add text.
        text (str):
            The message to insert.
        pos_x (float):
            Distance from left border to first character.
        pos_y (float):
            Distance from bottom border to first character.
        font_size (float):
            Font size the text shall have.
        font_info (FontInfo):
            Font data and information.
        pdf_font (``FPDF_FONT``):
            PDFium font object handle.
    """
    
    page = open_page(pdf, page_index)
    
    hb_buffer = harfbuzz.Buffer()
    hb_buffer.add_str(text)
    hb_buffer.guess_segment_properties()
    hb_features = {"kern": True, "liga": True}
    harfbuzz.shape(font_info.hb_font, hb_buffer, hb_features)
    
    start_point = pos_x
    for info, pos in zip(hb_buffer.glyph_infos, hb_buffer.glyph_positions):
        pdf_textobj = pdfium.FPDFPageObj_CreateTextObj(pdf, pdf_font, font_size)
        pdfium.FPDFText_SetCharcodes(pdf_textobj, ctypes.c_uint32(info.codepoint), 1)
        pdfium.FPDFPageObj_Transform(
            pdf_textobj,
            1, 0, 0, 1,
            start_point - (pos.x_offset / font_info.hb_scale) * font_size,
            pos_y,
        )
        pdfium.FPDFPage_InsertObject(page, pdf_textobj)
        start_point += (pos.x_advance / font_info.hb_scale) * font_size
    
    pdfium.FPDFPage_GenerateContent(page)
