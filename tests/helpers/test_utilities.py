# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause 

import pytest
import pypdfium2 as pdfium


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (0, 0),
        (90, 1),
        (180, 2),
        (270, 3),
    ]
)
def test_translate_rotation(test_input, expected):
    translated = pdfium.translate_rotation(test_input)
    assert translated == expected


@pytest.mark.parametrize(
    "values, expected",
    [
        ((255, 255, 255, 255), (0xFFFFFFFF, False)),
        ((255, 255, 255), (0xFFFFFFFF, False)),
        ((0, 255, 255, 255), (0xFF00FFFF, False)),
        ((255, 0, 255, 255), (0xFFFF00FF, False)),
        ((255, 255, 0, 255), (0xFFFFFF00, False)),
        ((255, 255, 255, 0), (0x00FFFFFF, True)),
    ]
)
def test_colour_to_hex(values, expected):
    assert pdfium.colour_as_hex(*values) == expected
