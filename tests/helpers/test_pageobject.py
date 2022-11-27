# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
from os.path import (
    join,
    exists,
)
import pytest
import PIL.Image
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c
from ..conftest import TestFiles, OutputDir


def test_image_objects():
    pdf = pdfium.PdfDocument(TestFiles.images)
    page = pdf.get_page(0)
    assert page.pdf is pdf
    
    images = list( page.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_IMAGE]) )
    assert len(images) == 3
    
    obj = images[0]
    assert isinstance(obj, pdfium.PdfObject)
    assert type(obj) is pdfium.PdfImage
    assert obj.type == pdfium_c.FPDF_PAGEOBJ_IMAGE
    assert isinstance(obj.raw, pdfium_c.FPDF_PAGEOBJECT)
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
        assert type(obj) is pdfium.PdfObject
        assert isinstance(obj.raw, pdfium_c.FPDF_PAGEOBJECT)
        assert obj.type in (pdfium_c.FPDF_PAGEOBJ_TEXT, pdfium_c.FPDF_PAGEOBJ_PATH)
        assert obj.level == 0
        assert obj.page is page
        assert obj.pdf is pdf
        pos = obj.get_pos()
        assert len(pos) == 4


def test_new_image_from_jpeg():
    
    pdf = pdfium.PdfDocument.new()
    page = pdf.new_page(240, 120)
    
    image_a = pdfium.PdfImage.new(pdf)
    buffer = open(TestFiles.mona_lisa, "rb")
    image_a.load_jpeg(buffer, autoclose=True)
    metadata = image_a.get_metadata()
    width, height = metadata.width, metadata.height
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
    pil_image_2 = bitmap.to_pil()
    assert (120, 120) == pil_image_1.size == pil_image_2.size == (bitmap.width, bitmap.height)
    assert "RGB" == pil_image_1.mode == pil_image_2.mode
    
    in_data = TestFiles.mona_lisa.read_bytes()
    out_buffer = io.BytesIO()
    image_a.extract(out_buffer)
    out_buffer.seek(0)
    out_data = out_buffer.read()
    assert in_data == out_data
    
    metadata = image_a.get_metadata()
    assert isinstance(metadata, pdfium_c.FPDF_IMAGEOBJ_METADATA)
    assert metadata.bits_per_pixel == 24  # 3 channels, 8 bits each
    assert metadata.colorspace == pdfium_c.FPDF_COLORSPACE_DEVICERGB
    assert metadata.height == 120
    assert metadata.width == 120
    assert metadata.horizontal_dpi == 72
    assert metadata.vertical_dpi == 72
    
    image_b = pdfium.PdfImage.new(pdf)
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
    out_path = OutputDir / "image_jpeg.pdf"
    pdf.save(out_path)
    assert exists(out_path)
    
    page._finalizer()
    pdf._finalizer()
    assert buffer.closed is True


def test_new_image_from_bitmap():
    
    src_pdf = pdfium.PdfDocument(TestFiles.render)
    src_page = src_pdf[0]
    dst_pdf = pdfium.PdfDocument.new()
    image_a = pdfium.PdfImage.new(dst_pdf)
    
    bitmap = src_page.render()
    w, h = bitmap.width, bitmap.height
    image_a.set_bitmap(bitmap)
    matrix = pdfium.PdfMatrix()
    matrix.scale(w, h)
    image_a.set_matrix(matrix)
    
    pil_image = PIL.Image.open(TestFiles.mona_lisa)
    bitmap = pdfium.PdfBitmap.from_pil(pil_image)
    image_b = pdfium.PdfImage.new(dst_pdf)
    matrix = pdfium.PdfMatrix()
    matrix.scale(bitmap.width, bitmap.height)
    image_b.set_matrix(matrix)
    image_b.set_bitmap(bitmap)
    
    dst_page = dst_pdf.new_page(w, h)
    dst_page.insert_object(image_a)
    dst_page.insert_object(image_b)
    dst_page.generate_content()
    
    out_path = OutputDir / "image_bitmap.pdf"
    dst_pdf.save(out_path)
    
    reopened_pdf = pdfium.PdfDocument(out_path)
    reopened_page = reopened_pdf[0]
    reopened_image = next( reopened_page.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_IMAGE]) )
    assert reopened_image.get_filters() == ["FlateDecode"]


def test_replace_image_with_jpeg():
    
    pdf = pdfium.PdfDocument(TestFiles.images)
    page = pdf.get_page(0)
    
    images = list( page.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_IMAGE]) )
    matrices = [img.get_matrix() for img in images]
    assert len(images) == 3
    image_1 = images[0]
    
    image_1.load_jpeg(TestFiles.mona_lisa, pages=[page])
    metadata = image_1.get_metadata()
    width, height = metadata.width, metadata.height
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
    output_path = OutputDir / "replace_images.pdf"
    pdf.save(output_path)
    assert exists(output_path)


@pytest.mark.parametrize(
    "render", [False, True]
)
def test_image_get_bitmap(render):
    
    pdf = pdfium.PdfDocument(TestFiles.images)
    page = pdf.get_page(0)
    
    all_images = list( page.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_IMAGE]) )
    image = all_images[0]
    
    metadata = image.get_metadata()
    assert metadata.width == 115
    assert metadata.height == 48
    assert round(metadata.horizontal_dpi) == 38
    assert round(metadata.vertical_dpi) == 38
    assert metadata.colorspace == pdfium_c.FPDF_COLORSPACE_DEVICEGRAY
    assert metadata.marked_content_id == 1
    assert metadata.bits_per_pixel == 1
    
    bitmap = image.get_bitmap(render=render)
    assert isinstance(bitmap, pdfium.PdfBitmap)
    
    if render:
        assert bitmap.format == pdfium_c.FPDFBitmap_BGRA
        assert bitmap.n_channels == 4
        assert bitmap.width == 216
        assert bitmap.height == 90
        assert bitmap.stride == 864
        assert bitmap.rev_byteorder is False
        output_path = join(OutputDir, "extract_rendered.png")
    else:
        assert bitmap.format == pdfium_c.FPDFBitmap_Gray
        assert bitmap.n_channels == 1
        assert bitmap.width == 115
        assert bitmap.height == 48
        assert bitmap.stride == 116
        assert bitmap.rev_byteorder is False
        output_path = join(OutputDir, "extract.png")
    
    pil_image = bitmap.to_pil()
    assert isinstance(pil_image, PIL.Image.Image)
    pil_image.save(output_path)
    assert exists(output_path)


def test_remove_image():
    
    pdf = pdfium.PdfDocument(TestFiles.images)
    page_1 = pdf.get_page(0)
    
    # TODO order images by position
    images = list( page_1.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_IMAGE]) )
    assert len(images) == 3
    
    # drop an image
    page_1.remove_object(images[0])
    
    # delete and re-insert an image in place
    page_1.remove_object(images[1])
    page_1.insert_object(images[1])
    
    page_1.generate_content()
    
    output_path = OutputDir / "test_remove_objects.pdf"
    pdf.save(output_path)
    assert exists(output_path)
