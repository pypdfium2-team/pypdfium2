# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause  

import io
from PIL import Image
from ..conftest import (
    TestFiles,
    iterate_testfiles,
)
import pypdfium2 as pdfium


def _pdfdoc_load(input_obj):
    doc = pdfium.PdfDocument(input_obj)
    page = pdfium.FPDF_LoadPage(doc.raw, 0)
    pdfium.FPDF_ClosePage(page)
    doc.close()


def test_pdfdoc_loadfiles():
    for filepath in iterate_testfiles():
        _pdfdoc_load(filepath)


def test_pdfdoc_renderpage():
    doc = pdfium.PdfDocument(TestFiles.render)
    image = doc.render_page_topil(0)
    assert isinstance(image, Image.Image)
    doc.close()


def test_pdfdoc_renderpdf():
    
    doc = pdfium.PdfDocument(TestFiles.multipage)
    
    i = 0
    for image, suffix in doc.render_pdf_topil():
        assert isinstance(image, Image.Image)
        assert isinstance(suffix, str)
        i+= 1
    assert i == 3
    
    doc.close()


def test_pdfdoc_save():
    doc = pdfium.PdfDocument(TestFiles.multipage)
    pdfium.FPDFPage_Delete(doc.raw, 0)
    buffer = io.BytesIO()
    doc.save(buffer)
    doc.close()
    assert buffer.tell() > 100000
    buffer.close()
