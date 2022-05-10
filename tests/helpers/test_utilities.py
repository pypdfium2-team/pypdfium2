# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause 

import pypdfium2 as pdfium


def test_translate_rotation():
    test_cases = [
        (0,   0),
        (90,  1),
        (180, 2),
        (270, 3),
    ]
    for input, expectation in test_cases:
        assert pdfium.translate_rotation(input) == expectation


def test_colour_to_hex():
    test_cases = [
        ((255, 255, 255),      (0xFFFFFFFF, False)),
        ((255, 255, 255, 255), (0xFFFFFFFF, False)),
        ((0,   255, 255, 255), (0xFF00FFFF, False)),
        ((255, 0,   255, 255), (0xFFFF00FF, False)),
        ((255, 255, 0,   255), (0xFFFFFF00, False)),
        ((255, 255, 255, 0  ), (0x00FFFFFF, True )),
    ]
    for values, expectation in test_cases:
        assert pdfium.colour_as_hex(*values) == expectation
