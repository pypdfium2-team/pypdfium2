# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2 as pdfium
from os.path import join
from ..conftest import TestFiles, OutputDir


def test_pageobj_placement():
    
    src_pdf = pdfium.PdfDocument(TestFiles.multipage)
    dest_pdf = pdfium.PdfDocument.new()
    
    width_a, height_a = src_pdf.get_page_size(0)
    pageobj_a = src_pdf.page_as_form(0, dest_pdf)
    assert isinstance(pageobj_a, pdfium.PdfPageObject)
    
    matrix_a = pdfium.PdfMatrix()
    matrix_a.scale(0.5, 0.5)
    matrix_a.translate(width_a/4, height_a/4)
    pageobj_a.set_matrix(matrix_a)
    
    dest_page_a = dest_pdf.new_page(width_a, height_a)
    dest_page_a.insert_object(pageobj_a)
    dest_page_a.generate_content()
    
    with open(join(OutputDir, "pageobj_placement.pdf"), "wb") as buf:
        dest_pdf.save(buf)
    
    for g in (dest_page_a, dest_pdf, src_pdf): g.close()
