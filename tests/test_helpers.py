# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import pytest
from configuration import TestFiles
from pypdfium2 import _helpers as helpers
from pypdfium2 import _pypdfium as pdfium


def test_pdfcontext():
    with helpers.PdfContext(TestFiles.test_render) as pdf:
        assert isinstance(pdf, pdfium.FPDF_DOCUMENT)
        assert pdfium.FPDF_GetPageCount(pdf) == 1


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
    translated = helpers._translate_rotation(test_input)
    assert translated == expected


def test_render_page():
    with helpers.PdfContext(TestFiles.test_render) as pdf:
        pil_image = helpers.render_page(pdf, 0)
    assert pil_image.mode == 'RGB'
    assert pil_image.size == (595, 842)
    assert pil_image.getpixel( (0, 0) ) == (255, 255, 255)
    assert pil_image.getpixel( (150, 180) ) == (129, 212, 26)
    assert pil_image.getpixel( (150, 390) ) == (42, 96, 153)
    assert pil_image.getpixel( (150, 570) ) == (128, 0, 128)
