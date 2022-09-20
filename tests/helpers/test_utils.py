# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
import pypdfium2 as pdfium
from pypdfium2._helpers._utils import *

# TODO test auto_bitmap_format() and color_tohex()


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
    ["prefix", "mapping"],
    [
        ("PDFDEST_VIEW_", ViewmodeMapping),
        ("FPDF_ERR_", ErrorMapping),
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
