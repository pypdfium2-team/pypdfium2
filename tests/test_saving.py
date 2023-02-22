# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import pytest
import pypdfium2 as pdfium
from .conftest import TestResources


def _get_saving_handler(version):
    
    pdf = pdfium.PdfDocument.new()
    size = (612, 792)
    pdf.new_page(*size)
    
    kwargs = {}
    if version:
        kwargs["version"] = version
    
    saved_pdf = yield pdf, kwargs
    if version:
        saved_pdf.get_version() == version
    assert len(saved_pdf) == 1
    assert saved_pdf.get_page_size(0) == size
    
    yield


def _save_tofile(version, tmp_path, use_str):
    
    handler = _get_saving_handler(version)
    pdf, kwargs = next(handler)
    
    path = tmp_path / "test_save_tofile.pdf"
    dest = str(path) if use_str else path
    
    pdf.save(dest, **kwargs)
    assert path.is_file()
    
    saved_pdf = pdfium.PdfDocument(path)
    handler.send(saved_pdf)
    # path.unlink()  # FIXME fails on Windows


parametrize_saving_version = pytest.mark.parametrize("version", [None, 14, 17])


def test_save_to_strpath(tmp_path):
    _save_tofile(15, tmp_path, use_str=True)


@parametrize_saving_version
def test_save_to_path(version, tmp_path):
    _save_tofile(version, tmp_path, use_str=False)


@parametrize_saving_version
def test_save_tobuffer(version):
    
    handler = _get_saving_handler(version)
    pdf, kwargs = next(handler)
    
    out_buffer = io.BytesIO()
    pdf.save(out_buffer, **kwargs)
    assert out_buffer.tell() > 100
    out_buffer.seek(0)
    
    saved_pdf = pdfium.PdfDocument(out_buffer, autoclose=True)
    handler.send(saved_pdf)


def test_save_deletion():
    
    # Regression test for BUG(96):
    # Make sure page deletions take effect when saving a document
    
    pdf = pdfium.PdfDocument(TestResources.multipage)
    assert len(pdf) == 3
    pdf.del_page(0)
    assert len(pdf) == 2
    
    buffer = io.BytesIO()
    pdf.save(buffer)
    buffer.seek(0)
    
    saved_pdf = pdfium.PdfDocument(buffer, autoclose=True)
    assert len(saved_pdf) == 2
    
    page = saved_pdf.get_page(0)
    textpage = page.get_textpage()
    assert textpage.get_text_bounded() == "Page\r\n2"
