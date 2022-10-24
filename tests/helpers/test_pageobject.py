# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from os.path import (
    join,
    exists,
)
import pytest
import PIL.Image
import pypdfium2 as pdfium
from ..conftest import TestFiles, OutputDir


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
    image_a.load_jpeg(buffer, autoclose=True)
    width, height = image_a.get_size()
    page.insert_object(image_a)
    
    assert len(pdf._data_holder) == 2
    assert pdf._data_closer == [buffer]
    
    assert image_a.get_matrix() == pdfium.PdfMatrix()
    matrix = pdfium.PdfMatrix()
    matrix.scale(width, height)
    image_a.set_matrix(matrix)
    assert image_a.get_matrix() == pdfium.PdfMatrix(width, 0, 0, height, 0, 0)
    
    pil_image_1 = PIL.Image.open(TestFiles.mona_lisa)
    bitmap = image_a.get_bitmap()
    info = bitmap.info
    pil_image_2 = bitmap.to_pil()
    assert (120, 120) == pil_image_1.size == pil_image_2.size == (info.width, info.height)
    assert "RGB" == pil_image_1.mode == pil_image_2.mode
    
    metadata = image_a.get_metadata()
    assert isinstance(metadata, pdfium.FPDF_IMAGEOBJ_METADATA)
    assert metadata.bits_per_pixel == 24  # 3 channels, 8 bits each
    assert metadata.colorspace == pdfium.FPDF_COLORSPACE_DEVICERGB
    assert metadata.height == 120
    assert metadata.width == 120
    assert metadata.horizontal_dpi == 72
    assert metadata.vertical_dpi == 72
    
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
    
    page._finalizer()
    pdf._finalizer()
    assert buffer.closed is True


def test_replace_image():
    
    pdf = pdfium.PdfDocument(TestFiles.images)
    page = pdf.get_page(0)
    
    images = [img for img in page.get_objects() if isinstance(img, pdfium.PdfImageObject)]
    matrices = [img.get_matrix() for img in images]
    assert len(images) == 3
    image_1 = images[0]
    
    buffer = open(TestFiles.mona_lisa, "rb")
    image_1.load_jpeg(buffer, pages=[page])
    width, height = image_1.get_size()
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


@pytest.mark.parametrize(
    "render", [False, True]
)
def test_extract_image(render):
    
    pdf = pdfium.PdfDocument(TestFiles.images)
    page = pdf.get_page(0)
    
    all_images = [img for img in page.get_objects() if isinstance(img, pdfium.PdfImageObject)]
    image = all_images[0]
    
    metadata = image.get_metadata()
    assert metadata.width == 115
    assert metadata.height == 48
    assert round(metadata.horizontal_dpi) == 38
    assert round(metadata.vertical_dpi) == 38
    assert metadata.colorspace == pdfium.FPDF_COLORSPACE_DEVICEGRAY
    assert metadata.marked_content_id == 1
    assert metadata.bits_per_pixel == 1
    
    bitmap = image.get_bitmap(render=render)
    info = bitmap.info
    assert isinstance(bitmap, pdfium.PdfBitmap)
    assert isinstance(info, pdfium.PdfBitmapInfo)
    
    if render:
        assert info.format == pdfium.FPDFBitmap_BGRA
        assert info.n_channels == 4
        assert info.width == 216
        assert info.height == 90
        assert info.stride == 864
        assert info.rev_byteorder is False
        output_path = join(OutputDir, "extract_rendered.png")
    else:
        assert info.format == pdfium.FPDFBitmap_Gray
        assert info.n_channels == 1
        assert info.width == 115
        assert info.height == 48
        assert info.stride == 116
        assert info.rev_byteorder is False
        output_path = join(OutputDir, "extract.png")
    
    pil_image = bitmap.to_pil()
    assert isinstance(pil_image, PIL.Image.Image)
    pil_image.save(output_path)
    assert exists(output_path)


def test_remove_image():
    
    pdf = pdfium.PdfDocument(TestFiles.images)
    page_1 = pdf.get_page(0)
    
    # TODO order images by position
    images = [img for img in page_1.get_objects() if isinstance(img, pdfium.PdfImageObject)]
    assert len(images) == 3
    
    # drop an image
    page_1.remove_object(images[0])
    
    # delete and re-insert an image in place
    page_1.remove_object(images[1])
    page_1.insert_object(images[1])
    
    page_1.generate_content()
    
    output_path = join(OutputDir, "test_remove_objects.pdf")
    with open(output_path, "wb") as buffer:
        pdf.save(buffer)
    assert exists(output_path)
