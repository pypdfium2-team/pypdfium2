# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import pytest
from .configuration import TestFiles
from pypdfium2 import _helpers as helpers
from pypdfium2 import _exceptions as exceptions
from pypdfium2 import _pypdfium as pdfium


def _check_pdf(pdf, page_count=1):
    assert isinstance(pdf, pdfium.FPDF_DOCUMENT)
    assert pdfium.FPDF_GetPageCount(pdf) == page_count


def test_pdfcontext():
    with helpers.PdfContext(TestFiles.test_render) as pdf:
        _check_pdf(pdf)

def test_open_encrypted():
    with helpers.PdfContext(TestFiles.test_encrypted, 'test_user') as pdf:
        _check_pdf(pdf)
    with helpers.PdfContext(TestFiles.test_encrypted, 'test_owner') as pdf:
        _check_pdf(pdf)


def test_open_encrypted_fail():
    with pytest.raises(exceptions.LoadPdfError, match="Missing or wrong password."):
        with helpers.PdfContext(TestFiles.test_encrypted, 'string') as pdf:
            pass


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


def test_render_normal():
    
    with helpers.PdfContext(TestFiles.test_render) as pdf:
        pil_image = helpers.render_page(pdf, 0)
    
    assert pil_image.mode == 'RGB'
    assert pil_image.size == (595, 842)
    assert pil_image.getpixel( (0, 0) ) == (255, 255, 255)
    assert pil_image.getpixel( (150, 180) ) == (129, 212, 26)
    assert pil_image.getpixel( (150, 390) ) == (42, 96, 153)
    assert pil_image.getpixel( (150, 570) ) == (128, 0, 128)
    
    pil_image.close()


def test_render_encrypted():
    
    with helpers.PdfContext(TestFiles.test_encrypted, 'test_user') as pdf:
        pil_image_a = helpers.render_page(pdf, 0)
    assert pil_image_a.mode == 'RGB'
    assert pil_image_a.size == (596, 842)
    
    with helpers.PdfContext(TestFiles.test_encrypted, 'test_owner') as pdf:
        pil_image_b = helpers.render_page(pdf, 0)
    assert pil_image_b.mode == 'RGB'
    assert pil_image_b.size == (596, 842)
    
    assert pil_image_a == pil_image_b
    
    pil_image_a.close()
    pil_image_b.close()


def test_render_alpha():
    
    with helpers.PdfContext(TestFiles.test_render) as pdf:
        pil_image = helpers.render_page(
            pdf, 0,
            background_colour = None,
        )
    
    assert pil_image.mode == 'RGBA'
    assert pil_image.size == (595, 842)
    assert pil_image.getpixel( (0, 0) ) == (0, 0, 0, 0)
    assert pil_image.getpixel( (62, 66) ) == (0, 0, 0, 186)
    assert pil_image.getpixel( (150, 180) ) == (129, 212, 26, 255)
    assert pil_image.getpixel( (150, 390) ) == (42, 96, 153, 255)
    assert pil_image.getpixel( (150, 570) ) == (128, 0, 128, 255)
    
    pil_image.close()
