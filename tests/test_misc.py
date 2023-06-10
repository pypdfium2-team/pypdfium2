# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i


@pytest.mark.parametrize(
    ["color_in", "rev_byteorder", "exp_color"],
    [
        ((170, 187, 204, 221), False, 0xDDAABBCC),
        ((170, 187, 204, 221), True, 0xDDCCBBAA),
    ]
)
def test_color_tohex(color_in, rev_byteorder, exp_color):
    
    assert pdfium_i.color_tohex(color_in, rev_byteorder) == exp_color
    
    # PDFium's utility macros just encode/decode the given color positionally, regardless of byte order
    r, g, b, a = color_in
    channels = (a, b, g, r) if rev_byteorder else (a, r, g, b)
    assert pdfium_c.FPDF_ARGB(*channels) == exp_color
    assert pdfium_c.FPDF_GetAValue(exp_color) == channels[0]
    assert pdfium_c.FPDF_GetRValue(exp_color) == channels[1]
    assert pdfium_c.FPDF_GetGValue(exp_color) == channels[2]
    assert pdfium_c.FPDF_GetBValue(exp_color) == channels[3]


def _filter(prefix, skips=[], type=int):
    items = []
    for attr in dir(pdfium_c):
        value = getattr(pdfium_c, attr)
        if not attr.startswith(prefix) or not isinstance(value, type) or value in skips:
            continue
        items.append(value)
    return items


BitmapNsp = _filter("FPDFBitmap_", [pdfium_c.FPDFBitmap_Unknown])
PageObjNsp = _filter("FPDF_PAGEOBJ_")


@pytest.mark.parametrize(
    ["mapping", "use_keys", "items"],
    [
        (pdfium_i.BitmapTypeToNChannels,   True,  BitmapNsp),
        (pdfium_i.BitmapTypeToStr,         True,  BitmapNsp),
        (pdfium_i.BitmapTypeToStrReverse,  True,  BitmapNsp),
        (pdfium_i.BitmapStrToConst,        False, BitmapNsp),
        (pdfium_i.BitmapStrReverseToConst, False, BitmapNsp),
        (pdfium_i.FormTypeToStr,           True,  _filter("FORMTYPE_", [pdfium_c.FORMTYPE_COUNT])),
        (pdfium_i.ColorspaceToStr,         True,  _filter("FPDF_COLORSPACE_")),
        (pdfium_i.ViewmodeToStr,           True,  _filter("PDFDEST_VIEW_")),
        (pdfium_i.ObjectTypeToStr,         True,  PageObjNsp),
        (pdfium_i.ObjectTypeToConst,       False, PageObjNsp),
        (pdfium_i.PageModeToStr,           True,  _filter("PAGEMODE_")),
        (pdfium_i.ErrorToStr,              True,  _filter("FPDF_ERR_")),
        (pdfium_i.UnsupportedInfoToStr,    True,  _filter("FPDF_UNSP_")),
    ]
)
def test_const_converters(mapping, use_keys, items):
    
    assert len(mapping) == len(items)
    
    container = mapping.keys() if use_keys else mapping.values()
    for item in items:
        assert item in container


@pytest.mark.parametrize(
    ["degrees", "const"],
    [
        (0,   0),
        (90,  1),
        (180, 2),
        (270, 3),
    ]
)
def test_const_converters_rotation(degrees, const):
    assert pdfium_i.RotationToConst[degrees] == const
    assert pdfium_i.RotationToDegrees[const] == degrees
