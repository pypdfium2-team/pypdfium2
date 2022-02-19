# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2 as pdfium
from .conftest import TestFiles


def _load_pages(pdf):
    n_pages = pdfium.FPDF_GetPageCount(pdf)
    return [pdfium.FPDF_LoadPage(pdf, i) for i in range(n_pages)]

def _close_pages(pages):
    for page in pages:
        pdfium.FPDF_ClosePage(page)


def _assert_boxes_eq(box, expected):
    #print(box)
    assert type(box) is type(expected)
    assert tuple( [round(val, 4) for val in box] ) == expected


def _check_boxes(pages, mediaboxes, cropboxes):
    
    assert len(pages) == len(mediaboxes) == len(cropboxes)
    
    for page, exp_mediabox in zip(pages, mediaboxes):
        _assert_boxes_eq(pdfium.get_mediabox(page), exp_mediabox)
        
    for page, exp_cropbox in zip(pages, cropboxes):
        _assert_boxes_eq(pdfium.get_cropbox(page), exp_cropbox)
    
    # todo: add test files that actually contain BleedBox, TrimBox, and ArtBox
    
    for page, exp_bleedbox in zip(pages, cropboxes):
        _assert_boxes_eq(pdfium.get_bleedbox(page), exp_bleedbox)
    
    for page, exp_trimbox in zip(pages, cropboxes):
        _assert_boxes_eq(pdfium.get_trimbox(page), exp_trimbox)
    
    for page, exp_artbox in zip(pages, cropboxes):
        _assert_boxes_eq(pdfium.get_artbox(page), exp_artbox)


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
