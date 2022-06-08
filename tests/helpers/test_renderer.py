# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import math
import logging
import PIL.Image
from os.path import join
import pytest
import pypdfium2 as pdfium
from ..conftest import TestFiles, OutputDir, ExpRenderPixels, get_members


@pytest.fixture
def sample_page():
    pdf = pdfium.PdfDocument(TestFiles.render)
    page = pdf.get_page(0)
    yield page
    [g.close() for g in (page, pdf)]


@pytest.fixture
def multipage_doc():
    pdf = pdfium.PdfDocument(TestFiles.multipage)
    yield pdf
    pdf.close()


def _check_pixels(pil_image, pixels):
    for pos, value in pixels:
        assert pil_image.getpixel(pos) == value


@pytest.mark.parametrize(
    ("name", "crop", "scale", "rotation"),
    [   
        ["01_r0",      (0,   0,   0,   0  ), 0.25, 0,   ],
        ["02_r90",     (0,   0,   0,   0  ), 0.5,  90,  ],
        ["03_r180",    (0,   0,   0,   0  ), 0.75, 180, ],
        ["04_r270",    (0,   0,   0,   0  ), 1,    270, ],
        ["05_cl",      (100, 0,   0,   0  ), 0.5,  0,   ],
        ["06_cb",      (0,   100, 0,   0  ), 0.5,  0,   ],
        ["07_cr",      (0,   0,   100, 0  ), 0.5,  0,   ],
        ["08_ct",      (0,   0,   0,   100), 0.5,  0,   ],
        ["09_r90_cb",  (0,   100,  0,  0  ), 0.5,  90,  ],
        ["10_r180_cr", (0,   0,   100, 0  ), 0.5,  180, ],
        ["11_r270_ct", (0,   0,   0,   100), 0.5,  270, ],
    ]
)
def test_render_page_transform(sample_page, name, crop, scale, rotation):
    pil_image = sample_page.render_topil(
        crop = crop,
        scale = scale,
        rotation = rotation,
    )
    pil_image.save( join(OutputDir, "%s.png" % name) )
    assert pil_image.mode == "RGB"
    
    c_left, c_bottom, c_right, c_top = [math.ceil(c*scale) for c in crop]
    w = math.ceil(595*scale)
    h = math.ceil(842*scale)
    if rotation in (90, 270):
        w, h = h, w
    
    c_w = w - c_left - c_right
    c_h = h - c_bottom - c_top
    assert pil_image.size == (c_w, c_h)
    
    pixels = []
    for (x, y), value in ExpRenderPixels:
        x, y = round(x*scale), round(y*scale)
        if rotation in (90, 270):
            x, y = y, x
        if rotation == 90:
            x = w-1 - x
        elif rotation == 180:
            x = w-1 - x
            y = h-1 - y
        elif rotation == 270:
            y = h-1 - y
        x -= c_left
        y -= c_top
        if 0 <= x < c_w and 0 <= y < c_h:
            pixels.append( ((x, y), value) )
    
    _check_pixels(pil_image, pixels)
    pil_image.close()


def test_render_page_alpha(sample_page):
    
    pixels = [
        [(0,   0  ), (0,   0,   0,   0  )],
        [(62,  66 ), (0,   0,   0,   186)],
        [(150, 180), (129, 212, 26,  255)],
        [(150, 390), (42,  96,  153, 255)],
        [(150, 570), (128, 0,   128, 255)],
    ]
    pil_image = sample_page.render_topil(colour=None)
    
    assert pil_image.mode == "RGBA"
    assert pil_image.size == (595, 842)
    for pos, exp_value in pixels:
        assert pil_image.getpixel(pos) == exp_value
    
    pil_image.close()


def test_render_page_greyscale(sample_page):

    image_a = sample_page.render_topil(
        greyscale = True,
        scale = 0.5
    )
    assert image_a.size == (298, 421)
    assert image_a.mode == "L"
    image_a.save(join(OutputDir, "greyscale.png"))
    image_a.close()
    
    # PDFium currently doesn't support LA, hence greyscale + alpha rendering results in RGBA
    image_b = sample_page.render_topil(
        greyscale = True,
        colour = None,
        scale = 0.5
    )
    assert image_b.size == (298, 421)
    assert image_b.mode == "RGBA"
    image_b.save(join(OutputDir, "greyscale_alpha.png"))
    image_b.close()


@pytest.mark.parametrize(
    "colour",
    [
        (255, 255, 255, 255),
        (60,  70,  80,  100),
        (255, 255, 255),
        (0,   255, 255),
        (255, 0,   255),
        (255, 255, 0  ),
    ]
)
def test_render_page_bgcolour(colour, sample_page):
    
    pil_image = sample_page.render_topil(colour=colour, scale=0.5)
    assert pil_image.size == (298, 421)
    
    px_colour = colour
    if len(colour) == 4:
        if colour[3] == 255:
            px_colour = colour[:-1]
    
    bg_pixel = pil_image.getpixel( (0, 0) )
    assert bg_pixel == px_colour
    
    pil_image.close()


def test_render_page_tobytes(sample_page):
    
    bytedata, cl_format, size = sample_page.render_tobytes(scale=0.5)
    
    assert isinstance(bytedata, bytes)
    assert cl_format == "BGR"
    assert size == (298, 421)
    assert len(bytedata) == size[0] * size[1] * len(cl_format)
    
    pil_image = PIL.Image.frombytes("RGB", size, bytedata, "raw", "BGR")
    assert pil_image.mode == "RGB"
    assert pil_image.size == (298, 421)
    assert isinstance(pil_image, PIL.Image.Image)
    pil_image.close()


def test_render_page_optimisation(sample_page):
    
    modes = get_members(pdfium.OptimiseMode)
    assert len(modes) == 3
    assert set(modes) == set([
        pdfium.OptimiseMode.NONE,
        pdfium.OptimiseMode.LCD_DISPLAY,
        pdfium.OptimiseMode.PRINTING,
    ])
    
    for mode in modes:
        pil_image = sample_page.render_topil(
            optimise_mode = mode,
            scale = 0.5,
        )
        assert isinstance(pil_image, PIL.Image.Image)
        pil_image.close()


def test_render_page_noantialias(sample_page):
    pil_image = sample_page.render_topil(
        no_antialias = ("text", "image", "path"),
        scale = 0.5,
    )
    assert isinstance(pil_image, PIL.Image.Image)
    pil_image.close()


@pytest.fixture
def render_pdffile_topil(multipage_doc):
    
    renderer = multipage_doc.render_topil(
        scale=0.5, greyscale=True,
    )
    imgs = []
    
    for image in renderer:
        assert isinstance(image, PIL.Image.Image)
        assert image.mode == "L"
        imgs.append(image)
    
    assert len(imgs) == 3
    yield imgs
    [image.close() for image in imgs]


@pytest.fixture
def render_pdffile_tobytes(multipage_doc):
    
    renderer = multipage_doc.render_tobytes(
        scale=0.5, greyscale=True,
    )
    imgs = []
    
    for imgdata, cl_format, size in renderer:
        assert cl_format == "L"
        assert isinstance(imgdata, bytes)
        assert len(imgdata) == size[0] * size[1] * len(cl_format)
        pil_image = PIL.Image.frombytes("L", size, imgdata, "raw", "L")
        imgs.append(pil_image)
    
    assert len(imgs) == 3
    yield imgs
    [image.close() for image in imgs]


def test_render_pdffile(render_pdffile_topil, render_pdffile_tobytes):
    for image_a, image_b in zip(render_pdffile_topil, render_pdffile_tobytes):
        assert image_a == image_b


def test_render_pdf_new(caplog):
    
    pdf = pdfium.PdfDocument.new()
    page = pdf.new_page(50, 100)
    
    with caplog.at_level(logging.WARNING):
        renderer = pdf.render_topil()
        image = next(renderer)
    
    warning = "Cannot perform concurrent processing without input sources - saving the document implicitly to get picklable data."
    assert warning in caplog.text
    
    assert isinstance(image, PIL.Image.Image)
    assert image.mode == "RGB"
    assert image.size == (50, 100)
    
    [g.close() for g in (image, page, pdf)]


def test_render_pdfbuffer(caplog):
    
    buffer = open(TestFiles.render, "rb")
    pdf = pdfium.PdfDocument(buffer)
    assert pdf._orig_input is buffer
    assert pdf._actual_input is buffer
    assert pdf._rendering_input is None
    
    with caplog.at_level(logging.WARNING):
        for image in pdf.render_topil(scale=0.5):
            assert isinstance(image, PIL.Image.Image)
    
    assert isinstance(pdf._rendering_input, bytes)
    warning = "Cannot perform concurrent rendering with buffer input - reading the whole buffer into memory implicitly."
    assert warning in caplog.text
    
    pdf.close()
    buffer.close()


def test_render_pdfbytes():
    
    with open(TestFiles.render, "rb") as fh:
        data = fh.read()
    
    pdf = pdfium.PdfDocument(data)
    assert pdf._orig_input is data
    assert pdf._actual_input is data
    assert pdf._rendering_input is None
    for image in pdf.render_topil(scale=0.5):
        assert isinstance(image, PIL.Image.Image)
    assert isinstance(pdf._rendering_input, bytes)
    
    pdf.close()


def test_render_pdffile_asbuffer():
    
    pdf = pdfium.PdfDocument(TestFiles.render, file_access=pdfium.FileAccess.BUFFER)
    
    assert pdf._orig_input == TestFiles.render
    assert isinstance(pdf._actual_input, io.BufferedReader)
    assert pdf._rendering_input is None
    assert pdf._file_access is pdfium.FileAccess.BUFFER
    
    for image in pdf.render_topil(scale=0.5):
        assert isinstance(image, PIL.Image.Image)
    
    # Not sure how to test that the requested file access strategy is actually used when constructing the new PdfDocument objects
    assert pdf._rendering_input == TestFiles.render
    
    pdf.close()
    assert pdf._actual_input.closed is True


def test_render_pdffile_asbytes():
    
    pdf = pdfium.PdfDocument(TestFiles.render, file_access=pdfium.FileAccess.BYTES)
    
    assert pdf._orig_input == TestFiles.render
    assert isinstance(pdf._actual_input, bytes)
    assert pdf._rendering_input is None
    assert pdf._file_access is pdfium.FileAccess.BYTES
    
    for image in pdf.render_topil(scale=0.5):
        assert isinstance(image, PIL.Image.Image)
    assert pdf._rendering_input == TestFiles.render
    
    pdf.close()
