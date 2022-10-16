# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from os.path import (
    join,
    exists,
)
import pytest
import pypdfium2 as pdfium
from ..conftest import TestFiles, OutputDir


def test_boxes():
    
    pdf = pdfium.PdfDocument(TestFiles.render)
    index = 0
    page = pdf.get_page(index)
    assert page.get_size() == pdf.get_page_size(index) == (595, 842)
    assert page.get_mediabox() == (0, 0, 595, 842)
    assert isinstance(page, pdfium.PdfPage)
    
    test_cases = [
        ("media", (0,  0,  612, 792)),
        ("media", (0,  0,  595, 842)),
        ("crop",  (10, 10, 585, 832)),
        ("bleed", (20, 20, 575, 822)),
        ("trim",  (30, 30, 565, 812)),
        ("art",   (40, 40, 555, 802)),
    ]
    
    for meth_name, exp_box in test_cases:
        getattr(page, "set_%sbox" % meth_name)(*exp_box)
        box = getattr(page, "get_%sbox" % meth_name)()
        assert pytest.approx(box) == exp_box


def test_mediabox_fallback():
    pdf = pdfium.PdfDocument(TestFiles.box_fallback)
    page = pdf.get_page(0)
    assert page.get_mediabox() == (0, 0, 612, 792)


def test_rotation():
    pdf = pdfium.PdfDocument.new()
    page = pdf.new_page(500, 800)
    for r in (90, 180, 270, 0):
        page.set_rotation(r)
        assert page.get_rotation() == r


def test_image_objects():
    pdf = pdfium.PdfDocument(TestFiles.images)
    page = pdf.get_page(0)
    assert page.pdf is pdf
    
    images = [obj for obj in page.get_objects() if obj.type == pdfium.FPDF_PAGEOBJ_IMAGE]
    assert len(images) == 3
    
    obj = images[0]
    assert isinstance(obj, pdfium.PdfPageObject)
    assert type(obj) is pdfium.PdfImageObject
    assert obj.type == pdfium.FPDF_PAGEOBJ_IMAGE
    assert isinstance(obj.raw, pdfium.FPDF_PAGEOBJECT)
    assert obj.level == 0
    assert obj.page is page
    assert obj.pdf is pdf
    
    positions = [img.get_pos() for img in images]
    exp_positions = [
        (133, 459, 350, 550),
        (48, 652, 163, 700),
        (204, 204, 577, 360),
    ]
    assert len(positions) == len(exp_positions)
    for pos, exp_pos in zip(positions, exp_positions):
        assert pytest.approx(pos, abs=1) == exp_pos


def test_misc_objects():
    
    pdf = pdfium.PdfDocument(TestFiles.render)
    page = pdf.get_page(0)
    assert page.pdf is pdf
    
    for obj in page.get_objects():
        assert type(obj) is pdfium.PdfPageObject
        assert isinstance(obj.raw, pdfium.FPDF_PAGEOBJECT)
        assert obj.type in (pdfium.FPDF_PAGEOBJ_TEXT, pdfium.FPDF_PAGEOBJ_PATH)
        assert obj.level == 0
        assert obj.page is page
        assert obj.pdf is pdf
        pos = obj.get_pos()
        assert len(pos) == 4


def test_new_jpeg():
    
    pdf = pdfium.PdfDocument.new()
    page = pdf.new_page(240, 120)
    
    image_a = pdfium.PdfImageObject.new(pdf)
    buffer = open(TestFiles.mona_lisa, "rb")
    width, height = image_a.load_jpeg(buffer, autoclose=True)
    
    assert len(pdf._data_holder) == 2
    assert pdf._data_closer == [buffer]
    
    assert image_a.get_matrix() == pdfium.PdfMatrix()
    matrix = pdfium.PdfMatrix()
    matrix.scale(width, height)
    image_a.set_matrix(matrix)
    assert image_a.get_matrix() == pdfium.PdfMatrix(width, 0, 0, height, 0, 0)
    page.insert_object(image_a)
    
    metadata = image_a.get_info()
    assert isinstance(metadata, pdfium.FPDF_IMAGEOBJ_METADATA)
    assert metadata.bits_per_pixel == 24  # 3 chanels, 8 bits each
    assert metadata.colorspace == pdfium.FPDF_COLORSPACE_DEVICERGB
    assert metadata.height == width == 120
    assert metadata.width == height == 120
    assert metadata.horizontal_dpi == 72
    assert metadata.vertical_dpi == 72
    
    bitmap = pdfium.FPDFImageObj_GetBitmap(image_a.raw)
    assert pdfium.FPDFBitmap_GetWidth(bitmap) == width
    assert pdfium.FPDFBitmap_GetHeight(bitmap) == height
    pdfium.FPDFBitmap_Destroy(bitmap)
    
    image_b = pdfium.PdfImageObject.new(pdf)
    with open(TestFiles.mona_lisa, "rb") as buffer:
        image_b.load_jpeg(buffer, inline=True, autoclose=False)
    
    assert image_b.get_matrix() == pdfium.PdfMatrix()
    matrix = pdfium.PdfMatrix()
    matrix.scale(width, height)
    matrix.translate(width, 0)
    image_b.set_matrix(matrix)
    image_b.get_matrix() == pdfium.PdfMatrix(width, 0, 0, height, width, 0)
    page.insert_object(image_b)
    
    page.generate_content()
    output_path = join(OutputDir, "load_jpeg.pdf")
    with open(output_path, "wb") as buf:
        pdf.save(buf)
    
    assert exists(output_path)
    
    page.close()
    pdf.close()
    assert buffer.closed is True
    


def test_replace_image():
    
    pdf = pdfium.PdfDocument(TestFiles.images)
    page = pdf.get_page(0)
    
    images = [img for img in page.get_objects() if isinstance(img, pdfium.PdfImageObject)]
    matrices = [img.get_matrix() for img in images]
    assert len(images) == 3
    
    buffer = open(TestFiles.mona_lisa, "rb")
    width, height = images[0].load_jpeg(buffer, pages=[page])
    assert matrices == [img.get_matrix() for img in images]
    
    # preserve the aspect ratio
    # this strategy only works if the matrix was just used for size/position
    for image, matrix in zip(images, matrices):
        w_scale = matrix.a / width
        h_scale = matrix.d / height
        scale = min(w_scale, h_scale)
        new_matrix = pdfium.PdfMatrix(width*scale, 0, 0, height*scale, matrix.e, matrix.f)
        image.set_matrix(new_matrix)
        assert image.get_matrix() == new_matrix
    
    page.generate_content()
    output_path = join(OutputDir, "replace_images.pdf")
    with open(output_path, "wb") as buf:
        pdf.save(buf)
    assert exists(output_path)
