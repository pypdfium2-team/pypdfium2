# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2._helpers as pdfium
import pypdfium2.internal as pdfium_i
from pypdfium2_cli.fonts import _show_fonts
# from ctypes import byref, c_int

def attach(parser):
    pass

def _iterate_standard_fonts():
    dummy_pdf = pdfium.PdfDocument.new()
    for fontname in pdfium.PdfFont.STANDARD_FONTS:
        fontobj = pdfium.PdfFont.load_standard(dummy_pdf, fontname)
        yield fontobj.get_base_name(), fontobj.get_family_name()

def main(args):
    
    print("# Default TTF map")
    ttfmap = pdfium.PdfDefaultTTFMap.value
    print(f"All Charsets: {sorted(pdfium_i.CharsetToStr.values())}")
    missing = set(pdfium_i.CharsetToStr.keys()).difference(ttfmap.keys())
    missing = [pdfium_i.CharsetToStr[k] for k in missing]
    print(f"Absent from map: {missing}")
    str_ttfmap = {pdfium_i.CharsetToStr[k]: v for k, v in ttfmap.items()}
    _show_fonts(("Charset", "Default font"), sorted(str_ttfmap.items()))
    
    # sfh = pdfium.PdfSysfontBase.SINGLETON
    # if sfh:
    #     for charset, fontname in ttfmap.items():
    #         sfh.MapFont(None, weight=0, bItalic=False, charset=charset, pitch_family=0, face=fontname, _ignored=byref(c_int(0)))
    
    print("\n# Standard fonts")
    _show_fonts(("Base name", "Family name"), _iterate_standard_fonts(), None)
