# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
import pypdfium2 as pdfium
from pypdfium2._helpers._utils import *


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
    assert RotationToConst[degrees] == const
    assert RotationToDegrees[const] == degrees


@pytest.mark.parametrize(
    ["use_alpha", "greyscale", "cl_src", "cl_dest", "cl_const"],
    [
        (False, False, "BGR",  "RGB",  pdfium.FPDFBitmap_BGR),
        (True,  False, "BGRA", "RGBA", pdfium.FPDFBitmap_BGRA),
        (False, True,  "L",    "L",    pdfium.FPDFBitmap_Gray),
        (True,  True,  "BGRA", "RGBA", pdfium.FPDFBitmap_BGRA),
    ]
)
def test_get_colourformat(use_alpha, greyscale, cl_src, cl_dest, cl_const):
    assert (cl_src, cl_const) == get_colourformat(use_alpha, greyscale)
    assert ColourMapping[cl_src] == cl_dest


@pytest.mark.parametrize(
    ["values", "cl_value", "use_alpha"],
    [
        ((255, 255, 255),      0xFFFFFFFF, False),
        ((255, 255, 255, 255), 0xFFFFFFFF, False),
        ((0,   255, 255, 255), 0xFF00FFFF, False),
        ((255, 0,   255, 255), 0xFFFF00FF, False),
        ((255, 255, 0,   255), 0xFFFFFF00, False),
        ((255, 255, 255, 0  ), 0x00FFFFFF, True ),
    ]
)
def test_colour_tohex(values, cl_value, use_alpha):
    assert colour_tohex(*values) == (cl_value, use_alpha)


@pytest.mark.parametrize(
    ["prefix", "mapping"],
    [
        ("PDFDEST_VIEW_", ViewmodeMapping),
        ("FPDF_ERR", ErrorMapping),
        ("FPDF_PAGEOBJ_", ObjtypeToName),
    ]
)
def test_const_tostring(prefix, mapping):
    viewmode_attrs = [a for a in dir(pdfium) if a.startswith(prefix)]
    assert len(viewmode_attrs) == len(mapping)
    for attr in viewmode_attrs:
        const = getattr(pdfium, attr)
        as_string = mapping[const]
        assert isinstance(const, int)
        assert isinstance(as_string, str)
