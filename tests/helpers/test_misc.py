# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
import pypdfium2.raw as pdfium_c
from pypdfium2._helpers._internal import consts


@pytest.mark.parametrize(
    ["degrees", "const"],
    [
        (0,   0),
        (90,  1),
        (180, 2),
        (270, 3),
    ]
)
def test_rotation_conversion(degrees, const):
    assert consts.RotationToConst[degrees] == const
    assert consts.RotationToDegrees[const] == degrees


def _filter_namespace(prefix, skips, type=int):
    items = []
    for attr in dir(pdfium_c):
        value = getattr(pdfium_c, attr)
        if not attr.startswith(prefix) or not isinstance(value, type) or value in skips:
            continue
        items.append(value)
    return items


@pytest.mark.parametrize(
    ["mapping", "prefix", "skips"],
    [
        (consts.BitmapTypeToNChannels, "FPDFBitmap_", [pdfium_c.FPDFBitmap_Unknown]),
        (consts.BitmapTypeToStr, "FPDFBitmap_", [pdfium_c.FPDFBitmap_Unknown]),
        (consts.BitmapTypeToStrReverse, "FPDFBitmap_", [pdfium_c.FPDFBitmap_Unknown]),
        (consts.ColorspaceToStr, "FPDF_COLORSPACE_", []),
        (consts.ViewmodeToStr, "PDFDEST_VIEW_", []),
        (consts.ErrorToStr, "FPDF_ERR_", []),
        (consts.ObjectTypeToStr, "FPDF_PAGEOBJ_", []),
    ]
)
def test_const_converters(prefix, mapping, skips):
    items = _filter_namespace(prefix, skips)
    assert len(items) == len(mapping)
    for item in items:
        assert item in mapping
