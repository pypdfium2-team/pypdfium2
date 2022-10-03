# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2 as pdfium
from os.path import join
from ..conftest import TestFiles, OutputDir


def test_pageobj_placement():
    
    src_pdf = pdfium.PdfDocument(TestFiles.multipage)
    width, height = src_pdf.get_page_size(0)
    
    dest_pdf = pdfium.PdfDocument.new()
    dest_page = dest_pdf.new_page(width, height)
    xobject = src_pdf.page_as_xobject(0, dest_pdf)
    
    pageobj_a = xobject.as_pageobject()
    matrix_a = pdfium.PdfMatrix(0.5, 0, 0, 0.5, 0, height/2)
    pageobj_a.set_matrix(matrix_a)  # same effect as transform()
    dest_page.insert_object(pageobj_a)
    
    pageobj_b = xobject.as_pageobject()
    matrix_b = pdfium.PdfMatrix(-0.5, 0, 0, 0.5, width, height/2)
    pageobj_b.set_matrix(matrix_b)  # same effect as transform()
    dest_page.insert_object(pageobj_b)
    
    pageobj_c = xobject.as_pageobject()
    matrix_c = pdfium.PdfMatrix(0.5, 0, 0, -0.5, 0, height/2)
    pageobj_c.transform(matrix_c)  # same effect as set_matrix()
    dest_page.insert_object(pageobj_c)
    
    pageobj_d = xobject.as_pageobject()
    matrix_d = pdfium.PdfMatrix(-0.5, 0, 0, -0.5, width, height/2)
    pageobj_d.transform(matrix_d) # same effect as set_matrix()
    dest_page.insert_object(pageobj_d)
    
    dest_page.generate_content()
    
    with open(join(OutputDir, "pageobj_placement.pdf"), "wb") as buf:
        dest_pdf.save(buf)
    
    for g in (dest_page, xobject, dest_pdf, src_pdf): g.close()
