# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import re
import shutil
import tempfile
import pytest
import PIL.Image
from os.path import join, abspath
import pypdfium2 as pdfium
from ..conftest import TestFiles, ExpRenderPixels


def _check_general(pdf, n_pages=1):
    assert isinstance(pdf, pdfium.PdfDocument)
    assert len(pdf) == n_pages


def _check_render(pdf):
    
    page = pdf.get_page(0)
    pil_image = page.render_topil()
    page.close()
    
    assert pil_image.mode == "RGB"
    assert pil_image.size == (595, 842)
    for pos, exp_value in ExpRenderPixels:
        assert pil_image.getpixel(pos) == exp_value
    
    return pil_image


@pytest.fixture
def open_filepath():
    pdf = pdfium.PdfDocument(TestFiles.render)
    _check_general(pdf)
    yield _check_render(pdf)
    pdf.close()


@pytest.fixture
def open_bytes():
    
    with open(TestFiles.render, "rb") as buffer:
        bytedata = buffer.read()
    
    assert isinstance(bytedata, bytes)
    pdf = pdfium.PdfDocument(bytedata)
    
    _check_general(pdf)
    yield _check_render(pdf)
    
    pdf.close()


@pytest.fixture
def open_buffer():
    
    buffer = open(TestFiles.render, "rb")
    pdf = pdfium.PdfDocument(buffer)
    
    _check_general(pdf)
    yield _check_render(pdf)
    
    pdf.close()
    assert buffer.closed is False
    buffer.close()


def test_opener_inputtypes(open_filepath, open_bytes, open_buffer):
    for img in (open_filepath, open_bytes, open_buffer):
        assert isinstance(img, PIL.Image.Image)
    assert open_filepath == open_bytes == open_buffer


def test_open_buffer_autoclose():
    
    buffer = open(TestFiles.render, "rb")
    pdf = pdfium.PdfDocument(buffer, autoclose=True)
    _check_general(pdf)
    
    pdf.close()
    assert buffer.closed is True


def test_open_encrypted():
    
    buffer = open(TestFiles.encrypted, "rb")
    bytedata = buffer.read()
    buffer.seek(0)
    
    test_cases = [
        (TestFiles.encrypted, "test_owner"),
        (TestFiles.encrypted, "test_user"),
        (bytedata, "test_owner"),
        (bytedata, "test_user"),
        (buffer, "test_owner"),
        (buffer, "test_user"),
    ]
    
    for input_data, password in test_cases:
        pdf = pdfium.PdfDocument(input_data, password)
        _check_general(pdf)
        pdf.close()
        if input_data is buffer:
            buffer.seek(0)
    
    buffer.close()
    
    with pytest.raises(pdfium.PdfiumError, match=re.escape("Loading the document failed (PDFium: Incorrect password error)")):
        pdf = pdfium.PdfDocument(TestFiles.encrypted, "wrong_password")
        pdf.close()


def test_open_nonascii():
    with tempfile.TemporaryDirectory(prefix="pypdfium2_") as tempdir:
        nonascii_file = join(tempdir, "tên file chứakýtự éèáàçß 发短信.pdf")
        shutil.copy(TestFiles.render, nonascii_file)
        pdf = pdfium.PdfDocument(nonascii_file)
        _check_general(pdf)
        pdf.close()


def test_open_new():
    
    dest_pdf = pdfium.PdfDocument.new()
    src_pdf = pdfium.PdfDocument(TestFiles.multipage)
    
    pdfium.FPDF_ImportPages(dest_pdf.raw, src_pdf.raw, b"1, 3", 0)
    assert len(dest_pdf) == 2
    
    [g.close() for g in (dest_pdf, src_pdf)]


def test_open_invalid():
    with pytest.raises(TypeError):
        pdf = pdfium.PdfDocument()
    with pytest.raises(TypeError, match="The input must be a file path string, bytes, or a byte buffer, but 'int' was given."):
        pdf = pdfium.PdfDocument(123)
    with pytest.raises(FileNotFoundError, match="File does not exist: '%s'" % abspath("invalid/path")):
        pdf = pdfium.PdfDocument("invalid/path")


def test_hierarchy():
    
    pdf = pdfium.PdfDocument(TestFiles.empty)
    assert isinstance(pdf, pdfium.PdfDocument)
    assert isinstance(pdf.raw, pdfium.FPDF_DOCUMENT)
    
    page = pdf.get_page(0)
    assert isinstance(page, pdfium.PdfPage)
    assert isinstance(page.raw, pdfium.FPDF_PAGE)
    assert page.pdf is pdf
    
    textpage = page.get_textpage()
    assert isinstance(textpage, pdfium.PdfTextPage)
    assert isinstance(textpage.raw, pdfium.FPDF_TEXTPAGE)
    assert textpage.page is page
    assert textpage.pdf is pdf
    
    searcher = textpage.search("abcd")
    assert isinstance(searcher, pdfium.PdfTextSearcher)
    assert searcher.textpage is textpage
    
    [g.close() for g in (searcher, textpage, page, pdf)]
