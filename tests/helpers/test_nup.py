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
    
    pageobj_a = src_pdf.page_as_form(0, dest_pdf)
    matrix_a = pdfium.PdfMatrix()
    matrix_a.scale(0.5, 0.5)
    matrix_a.translate(0, height/2)
    pageobj_a.set_matrix(matrix_a)
    dest_page.insert_object(pageobj_a)
    
    pageobj_b = src_pdf.page_as_form(0, dest_pdf)
    matrix_b = pdfium.PdfMatrix()
    matrix_b.scale(0.5, 0.5)
    matrix_b.translate(width/2, height/2)
    matrix_b.mirror(x=True, y=False)
    matrix_b.translate(width/2, 0)  # compensate
    pageobj_b.set_matrix(matrix_b)
    dest_page.insert_object(pageobj_b)
    
    pageobj_c = src_pdf.page_as_form(0, dest_pdf)
    matrix_c = pdfium.PdfMatrix()
    matrix_c.scale(0.5, 0.5)
    matrix_c.mirror(x=False, y=True)
    matrix_c.translate(0, height/2)  # compensate
    pageobj_c.set_matrix(matrix_c)
    dest_page.insert_object(pageobj_c)
    
    dest_page.generate_content()
    dest_page.close()
    
    with open(join(OutputDir, "pageobj_placement.pdf"), "wb") as buf:
        dest_pdf.save(buf)
    
    for g in (dest_pdf, src_pdf): g.close()
