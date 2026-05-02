# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
import pypdfium2._helpers as pdfium
import pypdfium2.internal as pdfium_i
from pypdfium2_cli.fonts import _show_table

def attach(parser):
    pass

def _iterate_standard_fonts():
    dummy_pdf = pdfium.PdfDocument.new()
    for fontname in pdfium.PdfFont.STANDARD_FONTS:
        fontobj = pdfium.PdfFont.load_standard(dummy_pdf, fontname)
        yield fontobj.get_base_name(), fontobj.get_family_name()

def _map_default_fonts(sfh, ttfmap):
    for charset, fontname in ttfmap.items():
        font_handle = sfh.MapFont(None, weight=0, bItalic=False, charset=charset, pitch_family=0, face=fontname, _ignored=ctypes.byref(ctypes.c_int(0)))
        if not font_handle:
            continue
        buf_size = sfh.GetFaceName(None, font_handle, None, 0)
        if not (buf_size > 0):
            continue
        buf = ctypes.create_string_buffer(buf_size)
        buf_ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))
        sfh.GetFaceName(None, font_handle, buf_ptr, buf_size)

def main(args):
    
    print("# Standard fonts")
    _show_table(("Base name", "Family name"), _iterate_standard_fonts(), None)
    
    print("\n# Default TTF map")
    print(f"All Charsets: {sorted(pdfium_i.CharsetToStr.values())}")
    ttfmap = pdfium.PdfDefaultTTFMap.value
    missing = set(pdfium_i.CharsetToStr.keys()).difference(ttfmap.keys())
    missing = [pdfium_i.CharsetToStr[k] for k in missing]
    print(f"Absent from map: {missing}")
    str_ttfmap = {pdfium_i.CharsetToStr[k]: v for k, v in ttfmap.items()}
    _show_table(("Charset", "Default font"), sorted(str_ttfmap.items()))
    
    # requires initial EnumFonts triggered through standard fonts above
    sfh = pdfium.PdfSysfontBase.SINGLETON
    if sfh:
        _map_default_fonts(sfh, ttfmap)
