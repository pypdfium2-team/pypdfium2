# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2._helpers as pdfium
import pypdfium2.internal as pdfium_i
from pypdfium2_cli.fonts import _show_fonts

def attach(parser):
    pass

def _iterate_standard_fonts():
    dummy_pdf = pdfium.PdfDocument.new()
    for fontname in pdfium.PdfFont.STANDARD_FONTS:
        fontobj = pdfium.PdfFont.load_standard(dummy_pdf, fontname)
        yield fontobj.get_base_name(), fontobj.get_family_name()

def main(args):
    print("# Default TTF map")
    print(f"All Charsets: {sorted(pdfium_i.CharsetToStr.values())}")
    missing = set(pdfium_i.CharsetToStr.keys()).difference(pdfium.PdfDefaultTTFMap.value.keys())
    missing = [pdfium_i.CharsetToStr[k] for k in missing]
    print(f"Absent from map: {missing}")
    str_ttfmap = {pdfium_i.CharsetToStr[k]: v for k, v in pdfium.PdfDefaultTTFMap.value.items()}
    _show_fonts(("Charset", "Default font"), sorted(str_ttfmap.items()))
    print("\n# Standard fonts")
    _show_fonts(("Base name", "Family name"), _iterate_standard_fonts(), None)
