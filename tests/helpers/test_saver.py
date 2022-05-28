# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
from os.path import join, isfile
import pypdfium2 as pdfium
from ..conftest import TestFiles, OutputDir


def test_save():
    
    src_pdf = pdfium.PdfDocument(TestFiles.multipage)
    new_pdf_raw = pdfium.FPDF_ImportNPagesToOne(
        src_pdf.raw,
        595, 842,
        2, 2,
    )
    
    new_pdf = pdfium.PdfDocument(new_pdf_raw)
    assert len(new_pdf) == 1
    page = new_pdf.get_page(0)
    assert page.get_size() == (595, 842)
    
    output_file = join(OutputDir, "tiling.pdf")
    with open(output_file, "wb") as buffer:
        new_pdf.save(buffer)
    assert isfile(output_file)
    
    [g.close() for g in (page, new_pdf, src_pdf)]


def test_save_withversion():
    
    pdf = pdfium.PdfDocument(TestFiles.multipage)
    pdf.del_page(1)
    
    buffer = io.BytesIO()
    pdf.save(buffer, version=17)
    pdf.close()
    
    buffer.seek(0)
    data = buffer.read()
    buffer.seek(0)
    
    exp_start = b"%PDF-1.7"
    exp_end = b"%EOF\r\n"
    assert data[:len(exp_start)] == exp_start
    assert data[-len(exp_end):] == exp_end
    
    reopened_pdf = pdfium.PdfDocument(buffer)
    assert len(reopened_pdf) == 2
    reopened_pdf.close()
    buffer.close()
    
