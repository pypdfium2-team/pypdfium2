# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import os.path
import ctypes
import pytest
import logging
from PIL import Image
import pypdfium2 as pdfium
from os.path import join
from .conftest import TestFiles, OutputDir


def _load_pdf(file_or_data, password=None, page_count=1):
    with pdfium.PdfContext(file_or_data, password) as pdf:
        assert isinstance(pdf, pdfium.FPDF_DOCUMENT)
        assert pdfium.FPDF_GetPageCount(pdf) == page_count


def _load_pages(pdf):
    n_pages = pdfium.FPDF_GetPageCount(pdf)
    return [pdfium.FPDF_LoadPage(pdf, i) for i in range(n_pages)]


def _close_pages(pages):
    for page in pages:
        pdfium.FPDF_ClosePage(page)


def test_pdfct_str():
    in_path = TestFiles.render
    assert isinstance(in_path, str)
    _load_pdf(in_path)


def test_pdfct_bytestring():
    with open(TestFiles.render, 'rb') as file:
        data = file.read()
        assert isinstance(data, bytes)
    _load_pdf(data)


def test_pdfct_bytesio():
    with open(TestFiles.render, 'rb') as file:
        buffer = io.BytesIO(file.read())
        assert isinstance(buffer, io.BytesIO)
    _load_pdf(buffer)
    assert buffer.closed == False
    assert buffer.tell() == 0
    buffer.close()


def test_pdfct_bufreader():
    with open(TestFiles.render, 'rb') as buf_reader:
        assert isinstance(buf_reader, io.BufferedReader)
        _load_pdf(buf_reader)
        assert buf_reader.closed == False
        assert buf_reader.tell() == 0


def test_pdfct_encrypted():
    _load_pdf(TestFiles.encrypted, 'test_user')
    _load_pdf(TestFiles.encrypted, 'test_owner')
    _load_pdf(TestFiles.encrypted, 'test_user'.encode('ascii'))
    _load_pdf(TestFiles.encrypted, 'test_user'.encode('UTF-8'))
    with open(TestFiles.encrypted, 'rb') as buf_reader:
        _load_pdf(buf_reader, password='test_user')


def test_pdfct_encrypted_fail():
    pw_err_context = pytest.raises(pdfium.PdfiumError, match="Missing or wrong password.")
    with pw_err_context:
        _load_pdf(TestFiles.encrypted)
    with pw_err_context:
        _load_pdf(TestFiles.encrypted, 'string')
    with pw_err_context:
        _load_pdf(TestFiles.encrypted, 'string'.encode('ascii'))
    with pw_err_context:
        _load_pdf(TestFiles.encrypted, 'string'.encode('UTF-8'))


def test_save_pdf_tobuffer():
    
    pdf = pdfium.open_pdf(TestFiles.multipage)
    pdfium.FPDFPage_Delete(pdf, ctypes.c_int(0))
    
    buffer = io.BytesIO()
    pdfium.save_pdf(pdf, buffer)
    buffer.seek(0)
    
    data = buffer.read()
    start = data[:8]
    end = data[-6:]
    
    print(start, end)
    
    assert start == b"%PDF-1.6"
    assert end == b"%EOF\r\n"
    
    pdfium.close_pdf(pdf)


def test_save_pdf_tofile():
    
    src_pdf = pdfium.open_pdf(TestFiles.cropbox)
    
    # perform n-up compositing
    dest_pdf = pdfium.FPDF_ImportNPagesToOne(
        src_pdf,
        ctypes.c_float(1190),  # width
        ctypes.c_float(1684),  # height
        ctypes.c_size_t(2),    # number of horizontal pages
        ctypes.c_size_t(2),    # number of vertical pages
    )
    
    output_path = join(OutputDir,'n-up.pdf')
    with open(output_path, 'wb') as file_handle:
        pdfium.save_pdf(dest_pdf, file_handle)
    
    for pdf in (src_pdf, dest_pdf):
        pdfium.close_pdf(pdf)
    
    assert os.path.isfile(output_path)


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


def test_render_page_normal():
    
    with pdfium.PdfContext(TestFiles.render) as pdf:
        pil_image = pdfium.render_page(
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
    
    with pdfium.PdfContext(TestFiles.encrypted, 'test_user') as pdf:
        pil_image_a = pdfium.render_page(pdf, 0)
    assert pil_image_a.mode == 'RGB'
    assert pil_image_a.size == (596, 842)
    
    with pdfium.PdfContext(TestFiles.encrypted, 'test_owner') as pdf:
        pil_image_b = pdfium.render_page(pdf, 0)
    assert pil_image_b.mode == 'RGB'
    assert pil_image_b.size == (596, 842)
    
    assert pil_image_a == pil_image_b
    
    pil_image_a.close()
    pil_image_b.close()


def test_render_page_alpha():
    
    with pdfium.PdfContext(TestFiles.render) as pdf:
        pil_image = pdfium.render_page(
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
        
        image_0 = pdfium.render_page(
            pdf, 0,
            rotation = 0
        )
        image_0.save(join(OutputDir,'rotate_0.png'))
        image_0.close()
        
        image_90 = pdfium.render_page(
            pdf, 0,
            rotation = 90
        )
        image_90.save(join(OutputDir,'rotate_90.png'))
        image_90.close()
        
        image_180 = pdfium.render_page(
            pdf, 0,
            rotation = 180
        )
        image_180.save(join(OutputDir,'rotate_180.png'))
        image_180.close()
        
        image_270 = pdfium.render_page(
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
    
    renderer = pdfium.render_pdf(
        TestFiles.multipage,
        colour = (255, 255, 255),
    )
    for image, suffix in renderer:
        assert isinstance(image, Image.Image)
        assert suffix == str(i+1).zfill(n_digits)
        image.close()
        i += 1


def test_render_pdf_bytes():
    
    with open(TestFiles.multipage, 'rb') as file_handle:
        file_bytes = file_handle.read()
    
    for image, suffix in pdfium.render_pdf(file_bytes):
        assert isinstance(image, Image.Image)
        assert image.mode == 'RGB'


def test_render_greyscale():
    
    with pdfium.PdfContext(TestFiles.render) as pdf:
        
        image_a = pdfium.render_page(
            pdf, 0,
            greyscale = True,
        )
        image_a.save(join(OutputDir,'greyscale.png'))
        assert image_a.mode == 'L'
        image_a.close()
        
        image_b = pdfium.render_page(
            pdf, 0,
            greyscale = True,
            colour = None,
        )
        assert image_b.mode == 'LA'
        image_b.save(join(OutputDir,'greyscale_alpha.png'))
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
    colour_int = pdfium.colour_as_hex(*values)
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
    
    with pdfium.PdfContext(TestFiles.render) as pdf:
        pil_image = pdfium.render_page(
            pdf, 0,
            colour = pdfium.colour_as_hex(*colour),
        )
    
    px_colour = colour
    if len(colour) == 4:
        if colour[3] == 255:
            px_colour = colour[:-1]
    
    bg_pixel = pil_image.getpixel( (0, 0) )
    assert bg_pixel == px_colour
    
    pil_image.close()


def test_read_toc():
    
    with pdfium.PdfContext(TestFiles.bookmarks) as pdf:
        toc = pdfium.get_toc(pdf)
        print()
        pdfium.print_toc(toc)


def test_read_toc_circular(caplog):
    
    with caplog.at_level(logging.CRITICAL):
        
        with pdfium.PdfContext(TestFiles.bookmarks_circular) as pdf:
            toc = pdfium.get_toc(pdf)
            print()
            pdfium.print_toc(toc)
            assert "circular bookmark reference" in caplog.text


def _assert_boxes_eq(box, expected):
    #print(box)
    assert type(box) is type(expected)
    assert tuple( [round(val, 4) for val in box] ) == expected


def _check_boxes(pages, mediaboxes, cropboxes):
    
    assert len(pages) == len(mediaboxes) == len(cropboxes)
    
    #print("Testing mediaboxes ...")
    for page, exp_mediabox in zip(pages, mediaboxes):
        _assert_boxes_eq(pdfium.get_mediabox(page), exp_mediabox)
        
    #print("Testing cropboxes ...")
    for page, exp_cropbox in zip(pages, cropboxes):
        _assert_boxes_eq(pdfium.get_cropbox(page), exp_cropbox)


def test_boxes_normal():
    
    with pdfium.PdfContext(TestFiles.multipage) as pdf:
        
        pages = _load_pages(pdf)
        boxes = (
            (0, 0, 595.2756, 841.8897),
            (0, 0, 595.2756, 419.5275),
            (0, 0, 297.6378, 419.5275),
        )
        
        _check_boxes(pages, boxes, boxes)
        _close_pages(pages)


def test_mediabox_fallback():
    
    with pdfium.PdfContext(TestFiles.mediabox_missing) as pdf:
        
        pages = _load_pages(pdf)
        boxes = (
            (0, 0, 612, 792),
            (0, 0, 612, 792),
        )
        
        _check_boxes(pages, boxes, boxes)
        _close_pages(pages)


def test_cropbox_different():
    
    with pdfium.PdfContext(TestFiles.cropbox) as pdf:
        
        pages = _load_pages(pdf)
        
        mediaboxes = [ (0, 0, 612, 792) for i in range(20)]
        for i in range(12, 16):
            mediaboxes[i] = (0, 0, 419.52, 595.32)
        
        cropboxes = [ (53, 35, 559, 757) for i in range(20)]
        for i in range(12, 16):
            cropboxes[i] = (48, 86, 371.52, 509.32)
        
        _check_boxes(pages, mediaboxes, cropboxes)
        _close_pages(pages)
