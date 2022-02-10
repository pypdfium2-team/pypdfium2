# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause  

import io
from PIL import Image
from .conftest import (
    TestFiles,
    iterate_testfiles,
)
import pypdfium2 as pdfium
from pypdfium2._cli.toc import print_toc


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
    image = doc.render_page(0)
    assert isinstance(image, Image.Image)
    doc.close()


def test_pdfdoc_renderpdf():
    
    doc = pdfium.PdfDocument(TestFiles.multipage)
    
    i = 0
    for image, suffix in doc.render_pdf():
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


def _compare_numarray(array, expected):
    assert type(array) is type(expected)
    assert len(array) == len(expected)
    for val_a, val_b in zip(array, expected):
        assert round(val_a) == val_b


def _compare_bookmark(
        bookmark,
        title,
        page_index,
        view_mode,
        view_pos,
    ):
    assert bookmark.title == title
    assert bookmark.page_index == page_index
    assert bookmark.view_mode == view_mode
    _compare_numarray(bookmark.view_pos, view_pos)


def test_pdfdoc_gettoc():
    
    doc = pdfium.PdfDocument(TestFiles.bookmarks)
    toc = doc.get_toc()
    
    # check first bookmark
    _compare_bookmark(
        next(toc),
        title = "One",
        page_index = 0,
        view_mode = pdfium.ViewMode.XYZ,
        view_pos = [89, 758, 0],
    )
    
    # check common values
    for bookmark in toc:
        assert isinstance(bookmark, pdfium.OutlineItem)
        assert bookmark.view_mode is pdfium.ViewMode.XYZ
        assert round(bookmark.view_pos[0]) == 89
    
    # check last bookmark
    _compare_bookmark(
        bookmark,
        title = "Three-B",
        page_index = 1,
        view_mode = pdfium.ViewMode.XYZ,
        view_pos = [89, 657, 0]
    )
    
    doc.close()


def test_pdfdoc_gettoc_maxdepth():
    
    doc = pdfium.PdfDocument(TestFiles.bookmarks)
    toc = doc.get_toc(max_depth=1)
    
    i = 0
    for bookmark in toc: i+= 1
    assert i == 3
    
    doc.close()


def test_pdfdoc_gettoc_print():
    doc = pdfium.PdfDocument(TestFiles.bookmarks)
    print_toc( doc.get_toc(max_depth=1) )
    doc.close()
