# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import io
import pytest
import pathlib
from .conftest import TestFiles
from pypdfium2 import _helpers as helpers
from pypdfium2 import _exceptions as exceptions
from pypdfium2 import _pypdfium as pdfium


def _open_pdf(file_or_data, password=None, page_count=1):
    with helpers.PdfContext(file_or_data, password) as pdf:
        assert isinstance(pdf, pdfium.FPDF_DOCUMENT)
        assert pdfium.FPDF_GetPageCount(pdf) == page_count


def test_pdfct_str():
    in_path = str(TestFiles.test_render)
    assert isinstance(in_path, str)
    _open_pdf(in_path)


def test_pdfct_pathlib():
    in_path = TestFiles.test_render
    assert isinstance(in_path, pathlib.Path)
    _open_pdf(in_path)


def test_pdfct_bytestring():
    with open(TestFiles.test_render, 'rb') as file:
        data = file.read()
        assert isinstance(data, bytes)
    _open_pdf(data)


def test_pdfct_bytesio():
    with open(TestFiles.test_render, 'rb') as file:
        buffer = io.BytesIO(file.read())
        assert isinstance(buffer, io.BytesIO)
    _open_pdf(buffer)
    assert buffer.closed == False
    assert buffer.tell() == 0
    buffer.close()


def test_pdfct_bufreader():
    with open(TestFiles.test_render, 'rb') as buf_reader:
        assert isinstance(buf_reader, io.BufferedReader)
        _open_pdf(buf_reader)
        assert buf_reader.closed == False
        assert buf_reader.tell() == 0


def test_pdfct_encrypted():
    _open_pdf(TestFiles.test_encrypted, 'test_user')
    _open_pdf(TestFiles.test_encrypted, 'test_owner')
    with open(TestFiles.test_encrypted, 'rb') as buf_reader:
        _open_pdf(buf_reader, password='test_user')


def test_pdfct_encrypted_fail():
    pw_err_context = pytest.raises(exceptions.LoadPdfError, match="Missing or wrong password.")
    with pw_err_context:
        _open_pdf(TestFiles.test_encrypted)
    with pw_err_context:
        _open_pdf(TestFiles.test_encrypted, 'string')


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
