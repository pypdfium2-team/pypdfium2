# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import math
import logging
from os.path import join
import numpy
import PIL.Image
import pytest
import pypdfium2 as pdfium
from ..conftest import (
    get_members,
    TestFiles,
    OutputDir,
    ExpRenderPixels
)


@pytest.fixture
def sample_page():
    pdf = pdfium.PdfDocument(TestFiles.render)
    page = pdf.get_page(0)
    yield page
    for g in (page, pdf): g.close()


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
    kwargs = dict(color=(0, 0, 0, 0))
    image = sample_page.render_topil(**kwargs)
    image_rev = sample_page.render_topil(**kwargs, rev_byteorder=True)
    
    assert image == image_rev
    assert image.mode == "RGBA"
    assert image.size == (595, 842)
    for pos, exp_value in pixels:
        assert image.getpixel(pos) == exp_value
    
    image.save(join(OutputDir, "colored_alpha.png"))
    for g in (image, image_rev): g.close()


def test_render_page_greyscale(sample_page):

    kwargs = dict(
        greyscale = True,
        scale = 0.5,
    )
    image = sample_page.render_topil(**kwargs)
    image_rev = sample_page.render_topil(**kwargs, rev_byteorder=True)
    assert image == image_rev
    assert image.size == (298, 421)
    assert image.mode == "L"
    image.save(join(OutputDir, "greyscale.png"))
    for g in (image, image_rev): g.close()
    
    # PDFium currently doesn't support LA, hence greyscale + alpha rendering results in RGBA
    image = sample_page.render_topil(
        greyscale = True,
        color = (0, 0, 0, 0),
        scale = 0.5,
    )
    assert image.size == (298, 421)
    assert image.mode == "RGBA"
    image.save(join(OutputDir, "greyscale_alpha.png"))
    image.close()


@pytest.mark.parametrize(
    "color",
    [
        (255, 255, 255, 255),
        (60,  70,  80,  100),
        (255, 255, 255, 255),
        (0,   255, 255, 255),
        (255, 0,   255, 255),
        (255, 255, 0,   255),
    ]
)
def test_render_page_bgcolor(color, sample_page):
    
    kwargs = dict(color=color, scale=0.5)
    image = sample_page.render_topil(**kwargs)
    image_rev = sample_page.render_topil(**kwargs, rev_byteorder=True)
    assert image == image_rev
    
    bg_pixel = image.getpixel( (0, 0) )
    if color[3] == 255:
        color = color[:-1]
    assert image.size == (298, 421)
    assert bg_pixel == color
    
    image.close()


def test_render_page_colorscheme():
    
    pdf = pdfium.PdfDocument(TestFiles.text)
    page = pdf.get_page(0)
    color_scheme = pdfium.ColorScheme(
        text_fill_color = (255, 255, 255, 255),
    )
    image = page.render_topil(
        greyscale = True,
        color = (0, 0, 0, 255),
        color_scheme = color_scheme,
    )
    assert image.mode == "L"
    image.save( join(OutputDir, "render_colorscheme.png") )
    
    for g in (page, pdf): g.close()


@pytest.mark.parametrize(
    "rev_byteorder", [False, True]
)
def test_render_page_tonumpy(rev_byteorder, sample_page):
    
    array, cl_format = sample_page.render_tonumpy(rev_byteorder=rev_byteorder)
    assert isinstance(array, numpy.ndarray)
    if rev_byteorder:
        assert cl_format == "RGB"
    else:
        assert cl_format == "BGR"
    
    for (x, y), value in ExpRenderPixels:
        if rev_byteorder:
            assert tuple(array[y][x]) == value
        else:
            assert tuple(array[y][x]) == tuple(reversed(value))


@pytest.mark.parametrize(
    "rev_byteorder", [False, True]
)
def test_render_page_tobytes(rev_byteorder, sample_page):
    
    bytedata, cl_format, size = sample_page.render_tobytes(scale=0.5, rev_byteorder=rev_byteorder)
    
    assert isinstance(bytedata, bytes)
    assert size == (298, 421)
    assert len(bytedata) == size[0] * size[1] * len(cl_format)
    if rev_byteorder:
        assert cl_format == "RGB"
    else:
        assert cl_format == "BGR"
    
    pil_image = PIL.Image.frombytes("RGB", size, bytedata, "raw", cl_format)
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
        no_smoothtext  = True,
        no_smoothimage = True,
        no_smoothpath  = True,
        scale = 0.5,
    )
    assert isinstance(pil_image, PIL.Image.Image)
    pil_image.close()


@pytest.fixture
def render_pdffile_topil(multipage_doc):
    
    renderer = multipage_doc.render_topil(scale=0.5)
    imgs = []
    
    for image in renderer:
        assert isinstance(image, PIL.Image.Image)
        assert image.mode == "RGB"
        imgs.append(image)
    
    assert len(imgs) == 3
    yield imgs
    for g in imgs: g.close()


@pytest.fixture
def render_pdffile_tobytes(multipage_doc):
    
    renderer = multipage_doc.render_tobytes(scale=0.5)
    imgs = []
    
    for imgdata, cl_format, size in renderer:
        assert cl_format == "BGR"
        assert isinstance(imgdata, bytes)
        assert len(imgdata) == size[0] * size[1] * len(cl_format)
        pil_image = PIL.Image.frombytes("RGB", size, imgdata, "raw", "BGR")
        imgs.append(pil_image)
    
    assert len(imgs) == 3
    yield imgs
    for g in imgs: g.close()


@pytest.fixture
def render_pdffile_tonumpy(multipage_doc):
    
    renderer = multipage_doc.render_tonumpy(scale=0.5, rev_byteorder=True)
    imgs = []
    
    for array, cl_format in renderer:
        assert cl_format == "RGB"
        assert isinstance(array, numpy.ndarray)
        # print(array)
        pil_image = PIL.Image.fromarray(array, mode=cl_format)
        imgs.append(pil_image)
    
    # for i, img in enumerate(imgs):
    #     img.save(join(OutputDir, "numpy_%s.png" % i))
    
    assert len(imgs) == 3
    yield imgs
    for g in imgs: g.close()


def test_render_pdffile(render_pdffile_topil, render_pdffile_tobytes, render_pdffile_tonumpy):
    for a, b, c in zip(render_pdffile_topil, render_pdffile_tobytes, render_pdffile_tonumpy):
        assert a == b == c


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
    
    for g in (image, page, pdf): g.close()


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
    
    for g in (pdf, buffer): g.close()


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
