# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import pytest
import pypdfium2 as pdfium
from .conftest import TestFiles


def _load_pdfct(file_or_data, password=None, page_count=1):
    with pdfium.PdfContext(file_or_data, password) as pdf:
        assert isinstance(pdf, pdfium.FPDF_DOCUMENT)
        assert pdfium.FPDF_GetPageCount(pdf) == page_count


def test_pdfct_str():
    in_path = TestFiles.render
    assert isinstance(in_path, str)
    _load_pdfct(in_path)


def test_pdfct_bytes():
    with open(TestFiles.render, 'rb') as file:
        data = file.read()
        assert isinstance(data, bytes)
    _load_pdfct(data)


def test_pdfct_bytesio():
    with open(TestFiles.render, 'rb') as file:
        buffer = io.BytesIO(file.read())
        assert isinstance(buffer, io.BytesIO)
    _load_pdfct(buffer)
    buffer.close()


def test_pdfct_bufreader():
    with open(TestFiles.render, 'rb') as buf_reader:
        assert isinstance(buf_reader, io.BufferedReader)
        _load_pdfct(buf_reader)


def test_pdfct_encrypted():
    _load_pdfct(TestFiles.encrypted, 'test_user')
    _load_pdfct(TestFiles.encrypted, 'test_owner')
    _load_pdfct(TestFiles.encrypted, 'test_user')
    with open(TestFiles.encrypted, 'rb') as buf_reader:
        _load_pdfct(buf_reader, password='test_user')


def test_pdfct_encrypted_fail():
    pw_err_context = pytest.raises(pdfium.PdfiumError, match="Missing or wrong password.")
    with pw_err_context:
        _load_pdfct(TestFiles.encrypted)
    with pw_err_context:
        _load_pdfct(TestFiles.encrypted, 'string')
    with pw_err_context:
        _load_pdfct(TestFiles.encrypted, 'string')


def test_open_native():
    
    pdf, ld_data = pdfium.open_pdf_native(TestFiles.multipage)
    
    # ensure that accessing the PDF works
    pdfium.FPDFPage_Delete(pdf, 1)
    page = pdfium.FPDF_LoadPage(pdf, 0)
    rotation = pdfium.FPDFPage_GetRotation(page)
    print( "Page {} has rotation {}".format(page, rotation) )
    pdfium.FPDF_ClosePage(page)
    
    pdfium.close_pdf(pdf, ld_data)


def test_open_nonascii_pdfct():
    _load_pdfct(TestFiles.nonascii)
