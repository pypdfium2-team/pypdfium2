# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
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
    version = pdf.get_version()
    assert isinstance(version, int)
    assert 10 < version < 30


def _check_render(pdf):
    
    page = pdf.get_page(0)
    pil_image = page.render_to(pdfium.BitmapConv.pil_image)
    page.close()
    
    assert pil_image.mode == "RGB"
    assert pil_image.size == (595, 842)
    for pos, exp_value in ExpRenderPixels:
        assert pil_image.getpixel(pos) == exp_value
    
    return pil_image


@pytest.fixture
def open_filepath_native():
    pdf = pdfium.PdfDocument(TestFiles.render)
    assert pdf._file_access is pdfium.FileAccess.NATIVE
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


def test_opener_inputtypes(open_filepath_native, open_bytes, open_buffer):
    first_image = open_filepath_native
    other_images = (
        open_bytes,
        open_buffer,
    )
    assert isinstance(first_image, PIL.Image.Image)
    assert all(first_image == other for other in other_images)


def test_open_buffer_autoclose():
    
    buffer = open(TestFiles.render, "rb")
    pdf = pdfium.PdfDocument(buffer, autoclose=True)
    _check_general(pdf)
    
    pdf.close()
    assert buffer.closed is True


def test_open_filepath_buffer():
    
    pdf = pdfium.PdfDocument(TestFiles.render, file_access=pdfium.FileAccess.BUFFER)
    
    assert pdf._orig_input == TestFiles.render
    assert isinstance(pdf._actual_input, io.BufferedReader)
    assert pdf._autoclose is True
    _check_general(pdf)
    
    pdf.close()
    assert pdf._actual_input.closed is True


def test_open_filepath_bytes():
    
    pdf = pdfium.PdfDocument(TestFiles.render, file_access=pdfium.FileAccess.BYTES)
    
    assert pdf._orig_input == TestFiles.render
    assert isinstance(pdf._actual_input, bytes)
    _check_general(pdf)
    
    pdf.close()


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


@pytest.mark.parametrize(
    "file_access",
    [pdfium.FileAccess.NATIVE, pdfium.FileAccess.BYTES, pdfium.FileAccess.BUFFER]
)
def test_open_nonencrypted_with_password(file_access):
    pdf = pdfium.PdfDocument(TestFiles.render, password="irrelevant", file_access=file_access)
    _check_general(pdf)
    pdf.close()


def test_open_nonascii():
    
    tempdir = tempfile.TemporaryDirectory(prefix="pypdfium2_")
    nonascii_file = join(tempdir.name, "tên file chứakýtự éèáàçß 发短信.pdf")
    shutil.copy(TestFiles.render, nonascii_file)
    
    pdf = pdfium.PdfDocument(nonascii_file)
    _check_general(pdf)
    pdf.close()
    
    tempdir.cleanup()


def test_open_new():
    
    dest_pdf = pdfium.PdfDocument.new()
    
    assert isinstance(dest_pdf, pdfium.PdfDocument)
    assert isinstance(dest_pdf.raw, pdfium.FPDF_DOCUMENT)
    assert dest_pdf.raw is dest_pdf._orig_input is dest_pdf._actual_input
    assert dest_pdf._rendering_input is None
    assert dest_pdf._ld_data is None
    
    assert dest_pdf.get_version() is None
    
    src_pdf = pdfium.PdfDocument(TestFiles.multipage)
    pdfium.FPDF_ImportPages(dest_pdf.raw, src_pdf.raw, b"1, 3", 0)
    assert len(dest_pdf) == 2
    
    for g in (dest_pdf, src_pdf): g.close()


def test_open_invalid():
    with pytest.raises(TypeError, match=re.escape("__init__() missing 1 required positional argument: 'input_data'")):
        pdf = pdfium.PdfDocument()
    with pytest.raises(TypeError, match=re.escape("Invalid input type 'int'")):
        pdf = pdfium.PdfDocument(123)
    with pytest.raises(FileNotFoundError, match=re.escape("File does not exist: '%s'" % abspath("invalid/path"))):
        pdf = pdfium.PdfDocument("invalid/path")
    with pytest.raises(FileNotFoundError, match=re.escape("File does not exist: '%s'" % abspath("invalid/path"))):
        pdf = pdfium.PdfDocument("invalid/path", file_access=pdfium.FileAccess.BUFFER)
    with pytest.raises(TypeError, match=re.escape("Invalid file_access type. Expected `FileAccess`, but got `str`.")):
        pdf = pdfium.PdfDocument(TestFiles.empty, file_access="abcd")


def test_object_hierarchy():
    
    pdf = pdfium.PdfDocument(TestFiles.images)
    assert isinstance(pdf, pdfium.PdfDocument)
    assert isinstance(pdf.raw, pdfium.FPDF_DOCUMENT)
    
    page = pdf.get_page(0)
    assert isinstance(page, pdfium.PdfPage)
    assert isinstance(page.raw, pdfium.FPDF_PAGE)
    assert page.pdf is pdf
    
    pageobj = next(page.get_objects())
    assert isinstance(pageobj, pdfium.PdfPageObject)
    assert isinstance(pageobj.raw, pdfium.FPDF_PAGEOBJECT)
    assert isinstance(pageobj.type, int)
    assert pageobj.page is page
    
    textpage = page.get_textpage()
    assert isinstance(textpage, pdfium.PdfTextPage)
    assert isinstance(textpage.raw, pdfium.FPDF_TEXTPAGE)
    assert textpage.page is page
    
    searcher = textpage.search("abcd")
    assert isinstance(searcher, pdfium.PdfTextSearcher)
    assert isinstance(searcher.raw, pdfium.FPDF_SCHHANDLE)
    assert searcher.textpage is textpage
    
    for g in (searcher, textpage, page, pdf): g.close()


def test_doc_extras():
    
    with pdfium.PdfDocument(TestFiles.empty, file_access=pdfium.FileAccess.BUFFER) as pdf:
        assert isinstance(pdf, pdfium.PdfDocument)
        assert len(pdf) == 1
        page = pdf[0]
        assert isinstance(page, pdfium.PdfPage)
        page.close()
    assert isinstance(pdf._actual_input, io.BufferedReader)
    assert pdf._actual_input.closed is True
    
    with pdfium.PdfDocument.new() as pdf:
        
        assert isinstance(pdf, pdfium.PdfDocument)
        assert len(pdf) == 0
        
        sizes = [(50, 100), (100, 150), (150, 200), (200, 250)]
        for size in sizes:
            page = pdf.new_page(*size)
            page.close()
        for i, (size, page) in enumerate(zip(sizes, pdf)):
            assert isinstance(page, pdfium.PdfPage)
            assert size == page.get_size() == pdf.get_page_size(i)
            page.close()
        
        del pdf[0]
        page = pdf[0]
        assert page.get_size() == pdf.get_page_size(0) == (100, 150)
        page.close()
        
        del pdf[-len(pdf)]
        page = pdf[-len(pdf)]
        assert page.get_size() == pdf.get_page_size(-len(pdf)) == (150, 200)
        page.close()
