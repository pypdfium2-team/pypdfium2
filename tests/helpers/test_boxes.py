# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2 as pdfium
from pytest import approx
from ..conftest import TestFiles


def _load_pages(pdf):
    n_pages = pdfium.FPDF_GetPageCount(pdf)
    return [pdfium.FPDF_LoadPage(pdf, i) for i in range(n_pages)]

def _close_pages(pages):
    for page in pages:
        pdfium.FPDF_ClosePage(page)


def _check_boxes(pages, mediaboxes, cropboxes):
    
    assert len(pages) == len(mediaboxes) == len(cropboxes)
    
    # todo: add test file that actually contains all boxes
    test_cases = [
        (pdfium.get_mediabox, mediaboxes),
        (pdfium.get_cropbox, cropboxes),
        (pdfium.get_bleedbox, cropboxes),
        (pdfium.get_trimbox, cropboxes),
        (pdfium.get_artbox, cropboxes),
    ]
    
    for func, boxes in test_cases:
        for page, exp_box in zip(pages, boxes):
            assert approx( func(page) ) == exp_box


def test_boxes_normal():
    with pdfium.PdfContext(TestFiles.multipage) as pdf:
        pages = _load_pages(pdf)
        boxes = (
            (0, 0, 595.2756, 841.8897),
            (0, 0, 595.2756, 419.5275),
            (0, 0, 297.6378, 419.5275),
        )
        _check_boxes(pages, boxes, boxes)
        _close_pages(pages)


def test_mediabox_fallback():
    with pdfium.PdfContext(TestFiles.mediabox_missing) as pdf:
        pages = _load_pages(pdf)
        boxes = (
            (0, 0, 612, 792),
            (0, 0, 612, 792),
        )
        _check_boxes(pages, boxes, boxes)
        _close_pages(pages)


def test_cropbox_different():
    
    with pdfium.PdfContext(TestFiles.cropbox) as pdf:
        
        pages = _load_pages(pdf)
        
        mediaboxes = [(0, 0, 612, 792) for i in range(20)]
        for i in range(12, 16):
            mediaboxes[i] = (0, 0, 419.52, 595.32)
        
        cropboxes = [(53, 35, 559, 757) for i in range(20)]
        for i in range(12, 16):
            cropboxes[i] = (48, 86, 371.52, 509.32)
        
        _check_boxes(pages, mediaboxes, cropboxes)
        _close_pages(pages)
