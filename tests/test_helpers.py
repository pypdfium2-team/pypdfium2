# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import pytest
import pathlib
import logging
from PIL import Image
from .conftest import TestFiles, OutputDir
from pypdfium2 import _helpers as helpers
from pypdfium2 import _exceptions as exceptions
from pypdfium2 import _pypdfium as pdfium


def _open_pdf(file_or_data, password=None, page_count=1):
    with helpers.PdfContext(file_or_data, password) as pdf:
        assert isinstance(pdf, pdfium.FPDF_DOCUMENT)
        assert pdfium.FPDF_GetPageCount(pdf) == page_count


def test_pdfct_str():
    in_path = str(TestFiles.render)
    assert isinstance(in_path, str)
    _open_pdf(in_path)


def test_pdfct_pathlib():
    in_path = TestFiles.render
    assert isinstance(in_path, pathlib.Path)
    _open_pdf(in_path)


def test_pdfct_bytestring():
    with open(TestFiles.render, 'rb') as file:
        data = file.read()
        assert isinstance(data, bytes)
    _open_pdf(data)


def test_pdfct_bytesio():
    with open(TestFiles.render, 'rb') as file:
        buffer = io.BytesIO(file.read())
        assert isinstance(buffer, io.BytesIO)
    _open_pdf(buffer)
    assert buffer.closed == False
    assert buffer.tell() == 0
    buffer.close()


def test_pdfct_bufreader():
    with open(TestFiles.render, 'rb') as buf_reader:
        assert isinstance(buf_reader, io.BufferedReader)
        _open_pdf(buf_reader)
        assert buf_reader.closed == False
        assert buf_reader.tell() == 0


def test_pdfct_encrypted():
    _open_pdf(TestFiles.encrypted, 'test_user')
    _open_pdf(TestFiles.encrypted, 'test_owner')
    _open_pdf(TestFiles.encrypted, 'test_user'.encode('ascii'))
    _open_pdf(TestFiles.encrypted, 'test_user'.encode('UTF-8'))
    with open(TestFiles.encrypted, 'rb') as buf_reader:
        _open_pdf(buf_reader, password='test_user')


def test_pdfct_encrypted_fail():
    pw_err_context = pytest.raises(exceptions.LoadPdfError, match="Missing or wrong password.")
    with pw_err_context:
        _open_pdf(TestFiles.encrypted)
    with pw_err_context:
        _open_pdf(TestFiles.encrypted, 'string')
    with pw_err_context:
        _open_pdf(TestFiles.encrypted, 'string'.encode('ascii'))
    with pw_err_context:
        _open_pdf(TestFiles.encrypted, 'string'.encode('UTF-8'))


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


def test_render_page_normal():
    
    with helpers.PdfContext(TestFiles.render) as pdf:
        pil_image = helpers.render_page(
            pdf, 0,
        )
    
    assert pil_image.mode == 'RGB'
    assert pil_image.size == (595, 842)
    assert pil_image.getpixel( (0, 0) ) == (255, 255, 255)
    assert pil_image.getpixel( (150, 180) ) == (129, 212, 26)
    assert pil_image.getpixel( (150, 390) ) == (42, 96, 153)
    assert pil_image.getpixel( (150, 570) ) == (128, 0, 128)
    
    pil_image.close()


def test_render_page_encrypted():
    
    with helpers.PdfContext(TestFiles.encrypted, 'test_user') as pdf:
        pil_image_a = helpers.render_page(pdf, 0)
    assert pil_image_a.mode == 'RGB'
    assert pil_image_a.size == (596, 842)
    
    with helpers.PdfContext(TestFiles.encrypted, 'test_owner') as pdf:
        pil_image_b = helpers.render_page(pdf, 0)
    assert pil_image_b.mode == 'RGB'
    assert pil_image_b.size == (596, 842)
    
    assert pil_image_a == pil_image_b
    
    pil_image_a.close()
    pil_image_b.close()


def test_render_page_alpha():
    
    with helpers.PdfContext(TestFiles.render) as pdf:
        pil_image = helpers.render_page(
            pdf, 0,
            colour = None,
        )
    
    assert pil_image.mode == 'RGBA'
    assert pil_image.size == (595, 842)
    assert pil_image.getpixel( (0, 0) ) == (0, 0, 0, 0)
    assert pil_image.getpixel( (62, 66) ) == (0, 0, 0, 186)
    assert pil_image.getpixel( (150, 180) ) == (129, 212, 26, 255)
    assert pil_image.getpixel( (150, 390) ) == (42, 96, 153, 255)
    assert pil_image.getpixel( (150, 570) ) == (128, 0, 128, 255)
    
    pil_image.close()


def test_render_page_rotation():
    
    with helpers.PdfContext(TestFiles.render) as pdf:
        
        image_0 = helpers.render_page(
            pdf, 0,
            rotation = 0
        )
        image_0.save(OutputDir/'rotate_0.png')
        image_0.close()
        
        image_90 = helpers.render_page(
            pdf, 0,
            rotation = 90
        )
        image_90.save(OutputDir/'rotate_90.png')
        image_90.close()
        
        image_180 = helpers.render_page(
            pdf, 0,
            rotation = 180
        )
        image_180.save(OutputDir/'rotate_180.png')
        image_180.close()
        
        image_270 = helpers.render_page(
            pdf, 0,
            rotation = 270
        )
        image_270.save(OutputDir/'rotate_270.png')
        image_270.close()
        


def test_render_pdf():
    
    with helpers.PdfContext(TestFiles.multipage) as pdf:
        n_pages = pdfium.FPDF_GetPageCount(pdf)
        
    n_digits = len(str(n_pages))
    i = 0
    
    renderer = helpers.render_pdf(
        TestFiles.multipage,
        colour = (255, 255, 255),
    )
    for image, suffix in renderer:
        assert isinstance(image, Image.Image)
        assert suffix == f"{i+1:0{n_digits}}"
        image.close()
        i += 1


def test_render_pdf_bytes():
    
    with open(TestFiles.multipage, 'rb') as file_handle:
        file_bytes = file_handle.read()
    
    for image, suffix in helpers.render_pdf(file_bytes):
        assert isinstance(image, Image.Image)
        assert image.mode == 'RGB'


def test_render_greyscale():
    
    with helpers.PdfContext(TestFiles.render) as pdf:
        
        image_a = helpers.render_page(
            pdf, 0,
            greyscale = True,
        )
        image_a.save(OutputDir/'greyscale.png')
        assert image_a.mode == 'L'
        image_a.close()
        
        image_b = helpers.render_page(
            pdf, 0,
            greyscale = True,
            colour = None,
        )
        assert image_b.mode == 'LA'
        image_b.save(OutputDir/'greyscale_alpha.png')
        image_b.close()


@pytest.mark.parametrize(
    "values, expected",
    [
        ((255, 255, 255, 255), 0xFFFFFFFF),
        ((255, 255, 255), 0xFFFFFFFF),
        ((0, 255, 255, 255), 0xFF00FFFF),
        ((255, 0, 255, 255), 0xFFFF00FF),
        ((255, 255, 0, 255), 0xFFFFFF00),
        ((255, 255, 255, 0), 0x00FFFFFF),
    ]
)
def test_colour_to_hex(values, expected):
    colour_int = helpers.colour_as_hex(*values)
    assert colour_int == expected


@pytest.mark.parametrize(
    "colour",
    [
        (255, 255, 255, 255),
        (60, 70, 80, 100),
        (255, 255, 255),
        (0, 255, 255),
        (255, 0, 255),
        (255, 255, 0),
    ]
)
def test_render_bgcolour(colour):
    
    with helpers.PdfContext(TestFiles.render) as pdf:
        pil_image = helpers.render_page(
            pdf, 0,
            colour = helpers.colour_as_hex(*colour),
        )
    
    px_colour = colour
    if len(colour) == 4:
        if colour[3] == 255:
            px_colour = colour[:-1]
    
    bg_pixel = pil_image.getpixel( (0, 0) )
    assert bg_pixel == px_colour
    
    pil_image.close()


def test_read_toc():
    
    with helpers.PdfContext(TestFiles.bookmarks) as pdf:
        toc = helpers.get_toc(pdf)
        print()
        helpers.print_toc(toc)


def test_read_toc_circular(caplog):
    
    with caplog.at_level(logging.CRITICAL):
        
        with helpers.PdfContext(TestFiles.bookmarks_circular) as pdf:
            toc = helpers.get_toc(pdf)
            print()
            helpers.print_toc(toc)
            assert "circular bookmark reference" in caplog.text
