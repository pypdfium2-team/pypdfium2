# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
from PIL import Image
from os.path import join
import pypdfium2 as pdfium
from .conftest import TestFiles, OutputDir


def _check_render_normal(pdf):
    
    pil_image = pdfium.render_page_topil(pdf, 0)
    
    assert pil_image.mode == 'RGB'
    assert pil_image.size == (595, 842)
    assert pil_image.getpixel( (0, 0) ) == (255, 255, 255)
    assert pil_image.getpixel( (150, 180) ) == (129, 212, 26)
    assert pil_image.getpixel( (150, 390) ) == (42, 96, 153)
    assert pil_image.getpixel( (150, 570) ) == (128, 0, 128)
    
    pil_image.close()


def test_render_page_filepath():
    with pdfium.PdfContext(TestFiles.render) as pdf:
        _check_render_normal(pdf)


def test_render_page_bytes():
    with open(TestFiles.render, 'rb') as fh:
        data = fh.read()
    with pdfium.PdfContext(data) as pdf:
        _check_render_normal(pdf)


def test_render_nonascii():
    with pdfium.PdfContext(TestFiles.nonascii) as pdf:
        pil_image = pdfium.render_page_topil(pdf, 0)
        pil_image.save( join(OutputDir,'render_nonascii.png') )


def _check_render_encrypted(file_or_data):
    
    with pdfium.PdfContext(file_or_data, 'test_user') as pdf:
        pil_image_a = pdfium.render_page_topil(pdf, 0)
    assert pil_image_a.mode == 'RGB'
    assert pil_image_a.size == (596, 842)
    
    with pdfium.PdfContext(file_or_data, 'test_owner') as pdf:
        pil_image_b = pdfium.render_page_topil(pdf, 0)
    assert pil_image_b.mode == 'RGB'
    assert pil_image_b.size == (596, 842)
    
    assert pil_image_a == pil_image_b
    
    pil_image_a.close()
    pil_image_b.close()


def test_render_page_encypted_file():
    _check_render_encrypted(TestFiles.encrypted)

def test_render_page_encrypted_bytes():
    with open(TestFiles.encrypted, 'rb') as fh:
        data = fh.read()
    _check_render_encrypted(data)


def test_render_page_alpha():
    
    with pdfium.PdfContext(TestFiles.render) as pdf:
        pil_image = pdfium.render_page_topil(
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
    
    with pdfium.PdfContext(TestFiles.render) as pdf:
        
        image_0 = pdfium.render_page_topil(
            pdf, 0,
            rotation = 0
        )
        image_0.save(join(OutputDir,'rotate_0.png'))
        image_0.close()
        
        image_90 = pdfium.render_page_topil(
            pdf, 0,
            rotation = 90
        )
        image_90.save(join(OutputDir,'rotate_90.png'))
        image_90.close()
        
        image_180 = pdfium.render_page_topil(
            pdf, 0,
            rotation = 180
        )
        image_180.save(join(OutputDir,'rotate_180.png'))
        image_180.close()
        
        image_270 = pdfium.render_page_topil(
            pdf, 0,
            rotation = 270
        )
        image_270.save(join(OutputDir,'rotate_270.png'))
        image_270.close()


def test_render_pdf():
    
    with pdfium.PdfContext(TestFiles.multipage) as pdf:
        n_pages = pdfium.FPDF_GetPageCount(pdf)
        
    n_digits = len(str(n_pages))
    i = 0
    
    renderer = pdfium.render_pdf_topil(
        TestFiles.multipage,
        colour = (255, 255, 255),
    )
    for image, suffix in renderer:
        assert isinstance(image, Image.Image)
        assert suffix == str(i+1).zfill(n_digits)
        image.close()
        i += 1


def test_render_pdf_frombytes():
    
    with open(TestFiles.multipage, 'rb') as file_handle:
        file_bytes = file_handle.read()
    
    for image, suffix in pdfium.render_pdf_topil(file_bytes):
        assert isinstance(image, Image.Image)
        assert isinstance(suffix, str)
        assert image.mode == 'RGB'
        image.close()


def test_render_greyscale():
    
    with pdfium.PdfContext(TestFiles.render) as pdf:
        
        image_a = pdfium.render_page_topil(
            pdf, 0,
            greyscale = True,
        )
        image_a.save(join(OutputDir,'greyscale.png'))
        assert image_a.mode == 'L'
        image_a.close()
        
        image_b = pdfium.render_page_topil(
            pdf, 0,
            greyscale = True,
            colour = None,
        )
        assert image_b.mode == 'RGBA'
        image_b.save(join(OutputDir,'greyscale_alpha.png'))
        image_b.close()


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
    
    with pdfium.PdfContext(TestFiles.render) as pdf:
        pil_image = pdfium.render_page_topil(
            pdf, 0,
            colour = colour,
        )
    
    px_colour = colour
    if len(colour) == 4:
        if colour[3] == 255:
            px_colour = colour[:-1]
    
    bg_pixel = pil_image.getpixel( (0, 0) )
    assert bg_pixel == px_colour
    
    pil_image.close()


def _abstest_render_tobytes(img_info):
    data, cl_format, size = img_info
    assert isinstance(data, bytes)
    assert isinstance(cl_format, str)
    assert 1 <= len(cl_format) <= 4
    assert all (c in ('RGBLA') for c in cl_format)
    assert len(size) == 2
    assert all(isinstance(s, int) for s in size)
    assert len(data) == size[0] * size[1] * len(cl_format)


def test_render_page_tobytes():
    with pdfium.PdfContext(TestFiles.render) as pdf:
        _abstest_render_tobytes( pdfium.render_page_tobytes(pdf, 0) )


def test_render_pdf_tobytes():
    for img_info, num in pdfium.render_pdf_tobytes(TestFiles.multipage):
        _abstest_render_tobytes(img_info)
        assert num.isdigit()
