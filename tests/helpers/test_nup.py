# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c
from ..conftest import TestFiles, OutputDir


def test_pageobj_placement():
    
    src_pdf = pdfium.PdfDocument(TestFiles.multipage)
    
    dest_pdf = pdfium.PdfDocument.new()
    xobject = src_pdf.page_as_xobject(0, dest_pdf)
    assert isinstance(xobject, pdfium.PdfXObject)
    assert isinstance(xobject.raw, pdfium_c.FPDF_XOBJECT)
    assert xobject.pdf is dest_pdf
    
    src_width, src_height = src_pdf.get_page_size(0)
    assert (round(src_width), round(src_height)) == (595, 842)
    w, h = src_width/2, src_height/2  # object size
    
    dest_page_1 = dest_pdf.new_page(src_width, src_height)
    
    po = xobject.as_pageobject()
    assert po.get_matrix() == pdfium.PdfMatrix()
    assert isinstance(po, pdfium.PdfObject)
    assert isinstance(po.raw, pdfium_c.FPDF_PAGEOBJECT)
    assert po.pdf is dest_pdf
    assert po.page is None
    assert po.type == pdfium_c.FPDF_PAGEOBJ_FORM
    matrix = pdfium.PdfMatrix()
    matrix.scale(0.5, 0.5)
    matrix.translate(0, h)  # position
    assert matrix == pdfium.PdfMatrix(0.5, 0, 0, 0.5, 0, h)
    po.set_matrix(matrix)
    assert po.get_matrix() == matrix
    dest_page_1.insert_object(po)
    assert po.pdf is dest_pdf
    assert po.page is dest_page_1
    pos_a = po.get_pos()
    # xfail with pdfium < 5370, https://crbug.com/pdfium/1905
    assert pytest.approx(pos_a, abs=0.5) == (19, 440, 279, 823)
    
    po = xobject.as_pageobject()
    matrix = pdfium.PdfMatrix()
    matrix.scale(0.5, 0.5)
    matrix.mirror(vertical=True, horizontal=False)
    matrix.translate(w, 0)  # compensate
    matrix.translate(w, h)  # position
    assert matrix == pdfium.PdfMatrix(-0.5, 0, 0, 0.5, 2*w, h)
    po.set_matrix(matrix)
    dest_page_1.insert_object(po)
    
    po = xobject.as_pageobject()
    assert po.get_matrix() == pdfium.PdfMatrix()
    matrix = pdfium.PdfMatrix()
    matrix.scale(0.5, 0.5)
    matrix.mirror(vertical=False, horizontal=True)
    matrix.translate(0, h)  # compensate
    matrix.translate(w, 0)  # position
    assert matrix == pdfium.PdfMatrix(0.5, 0, 0, -0.5, w, h)
    po.transform(matrix)
    assert po.get_matrix() == matrix
    dest_page_1.insert_object(po)
    
    po = xobject.as_pageobject()
    matrix = pdfium.PdfMatrix()
    matrix.scale(0.5, 0.5)
    matrix.mirror(vertical=True, horizontal=True)
    matrix.translate(w, h)  # compensate
    assert matrix == pdfium.PdfMatrix(-0.5, 0, 0, -0.5, w, h)
    po.transform(matrix)
    dest_page_1.insert_object(po)
    
    dest_page_1.generate_content()
    square_len = w + h
    dest_page_2 = dest_pdf.new_page(square_len, square_len)
    
    po = xobject.as_pageobject()
    matrix = pdfium.PdfMatrix()
    matrix.scale(0.5, 0.5)
    matrix.rotate(360)
    matrix.translate(0, w)  # position
    assert pytest.approx(matrix.get()) == (0.5, 0, 0, 0.5, 0, w)
    po.set_matrix(matrix)
    dest_page_2.insert_object(po)
    
    po = xobject.as_pageobject()
    matrix = pdfium.PdfMatrix()
    matrix.scale(0.5, 0.5)
    matrix.rotate(90)
    matrix.translate(0, w)  # compensate
    matrix.translate(w, h)  # position
    assert pytest.approx(matrix.get()) == (0, -0.5, 0.5, 0, w, w+h)
    po.set_matrix(matrix)
    dest_page_2.insert_object(po)
    
    po = xobject.as_pageobject()
    matrix = pdfium.PdfMatrix()
    matrix.scale(0.5, 0.5)
    matrix.rotate(180)
    matrix.translate(w, h)  # compensate
    matrix.translate(h, 0)  # position
    assert pytest.approx(matrix.get()) == (-0.5, 0, 0, -0.5, w+h, h)
    po.set_matrix(matrix)
    dest_page_2.insert_object(po)
    
    po = xobject.as_pageobject()
    matrix = pdfium.PdfMatrix()
    matrix.scale(0.5, 0.5)
    matrix.rotate(270)
    matrix.translate(h, 0)  # compensate
    assert pytest.approx(matrix.get()) == (0, 0.5, -0.5, 0, h, 0)
    po.set_matrix(matrix)
    dest_page_2.insert_object(po)
    
    dest_page_2.generate_content()
    dest_page_3 = dest_pdf.new_page(src_width, src_height)
    
    po = xobject.as_pageobject()
    matrix = pdfium.PdfMatrix()
    matrix.scale(0.5, 0.5)
    matrix.translate(-w/2, -h/2)
    matrix.rotate(90)
    matrix.translate(h/2, w/2)
    po.set_matrix(matrix)
    dest_page_3.insert_object(po)
    
    dest_page_3.generate_content()
    
    # TODO
    # * test copy and repr
    # * test skew
    # * assert that PdfObject.transform() actually transforms and is not just doing the same as set_matrix()
    # * assert that the transformation operates from the origin of the coordinate system
    
    dest_pdf.save(OutputDir / "pageobj_placement.pdf")
