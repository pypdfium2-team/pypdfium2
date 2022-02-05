# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause 

import io
import os
import ctypes
from os.path import join
import pypdfium2 as pdfium
from .conftest import TestFiles, OutputDir


def test_save_pdf_tobuffer():
    
    pdf = pdfium.open_pdf(TestFiles.multipage)
    pdfium.FPDFPage_Delete(pdf, ctypes.c_int(0))
    
    buffer = io.BytesIO()
    pdfium.save_pdf(pdf, buffer)
    buffer.seek(0)
    
    data = buffer.read()
    
    exp_start = b"%PDF-1.6"
    exp_end = b"%EOF\r\n"
    
    assert data[:len(exp_start)] == b"%PDF-1.6"
    assert data[-len(exp_end):] == b"%EOF\r\n"
    
    pdfium.close_pdf(pdf)


def test_save_pdf_tofile():
    
    src_pdf = pdfium.open_pdf(TestFiles.cropbox)
    
    # page tiling (n-up)
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
