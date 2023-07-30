# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import math
import numpy
import warnings
import PIL.Image
import pytest
import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c
from .conftest import (
    TestFiles,
    PyVersion,
    OutputDir,
    ExpRenderPixels
)

# TODO assert that bitmap and info are consistent


@pytest.fixture
def sample_page():
    pdf = pdfium.PdfDocument(TestFiles.render)
    page = pdf[0]
    yield page


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
    pil_image = sample_page.render(
        crop = crop,
        scale = scale,
        rotation = rotation,
    ).to_pil()
    pil_image.save(OutputDir / ("%s.png" % name))
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


@pytest.mark.parametrize(
    "rev_byteorder", [False, True]
)
def test_render_page_bgrx(rev_byteorder, sample_page):
    pil_image = sample_page.render(
        prefer_bgrx = True,
        rev_byteorder = rev_byteorder,
    ).to_pil()
    assert pil_image.mode == "RGBX"
    exp_pixels = [(pos, (*value, 255)) for pos, value in ExpRenderPixels]
    _check_pixels(pil_image, exp_pixels)


def test_render_page_alpha(sample_page):
    
    pixels = [
        [(0,   0  ), (0,   0,   0,   0  )],
        [(62,  66 ), (0,   0,   0,   186)],
        [(150, 180), (129, 212, 26,  255)],
        [(150, 390), (42,  96,  153, 255)],
        [(150, 570), (128, 0,   128, 255)],
    ]
    kwargs = dict(
        fill_color = (0, 0, 0, 0),
    )
    image = sample_page.render(**kwargs).to_pil()
    image_rev = sample_page.render(**kwargs, rev_byteorder=True).to_pil()
    
    if PyVersion > (3, 6):
        assert image == image_rev
    assert image.mode == "RGBA"
    assert image.size == (595, 842)
    for pos, exp_value in pixels:
        assert image.getpixel(pos) == exp_value
    
    image.save(OutputDir / "colored_alpha.png")


def test_render_page_grey(sample_page):
    kwargs = dict(
        grayscale = True,
        scale = 0.5,
    )
    image = sample_page.render(**kwargs).to_pil()
    image_rev = sample_page.render(**kwargs, rev_byteorder=True).to_pil()
    assert image == image_rev
    assert image.size == (298, 421)
    assert image.mode == "L"
    image.save(OutputDir / "grayscale.png")


@pytest.mark.parametrize(
    "fill_color",
    [
        (255, 255, 255, 255),
        (60,  70,  80,  100),
        (255, 255, 255, 255),
        (0,   255, 255, 255),
        (255, 0,   255, 255),
        (255, 255, 0,   255),
    ]
)
def test_render_page_fill_color(fill_color, sample_page):
    kwargs = dict(
        fill_color = fill_color,
        scale = 0.5,
    )
    image = sample_page.render(**kwargs).to_pil()
    image_rev = sample_page.render(**kwargs, rev_byteorder=True).to_pil()
    
    if PyVersion > (3, 6):
        assert image == image_rev
    
    bg_pixel = image.getpixel( (0, 0) )
    if fill_color[3] == 255:
        fill_color = fill_color[:-1]
    assert image.size == (298, 421)
    assert bg_pixel == fill_color


def test_render_page_colorscheme():
    pdf = pdfium.PdfDocument(TestFiles.text)
    page = pdf[0]
    color_scheme = pdfium.PdfColorScheme(
        path_fill   = (15,  15,  15,  255),
        path_stroke = (255, 255, 255, 255),
        text_fill   = (255, 255, 255, 255),
        text_stroke = (255, 255, 255, 255),
    )
    image = page.render(
        grayscale = True,
        fill_color = (0, 0, 0, 255),
        color_scheme = color_scheme,
    ).to_pil()
    assert image.mode == "L"
    image.save(OutputDir / "render_colorscheme.png")


@pytest.mark.parametrize(
    "rev_byteorder", [False, True]
)
def test_render_page_tonumpy(rev_byteorder, sample_page):
    
    bitmap = sample_page.render(
        rev_byteorder = rev_byteorder,
    )
    array = bitmap.to_numpy()
    assert isinstance(array, numpy.ndarray)
    if rev_byteorder:
        assert bitmap.mode == "RGB"
    else:
        assert bitmap.mode == "BGR"
    
    for (x, y), value in ExpRenderPixels:
        if rev_byteorder:
            assert tuple(array[y][x]) == value
        else:
            assert tuple(array[y][x]) == tuple(reversed(value))


@pytest.mark.parametrize("mode", [None, "lcd", "print"])
def test_render_page_optimization(sample_page, mode):
    pil_image = sample_page.render(
        optimize_mode = mode,
        scale = 0.5,
    ).to_pil()
    assert isinstance(pil_image, PIL.Image.Image)


def test_render_page_noantialias(sample_page):
    pil_image = sample_page.render(
        no_smoothtext  = True,
        no_smoothimage = True,
        no_smoothpath  = True,
        scale = 0.5,
    ).to_pil()
    assert isinstance(pil_image, PIL.Image.Image)


def test_render_pages_no_concurrency():
    pdf = pdfium.PdfDocument(TestFiles.multipage)
    for page in pdf:
        image = page.render(
            scale = 0.5,
            grayscale = True,
        ).to_pil()
        assert isinstance(image, PIL.Image.Image)


@pytest.mark.parametrize(
    ("with_forms", "exp_color"),
    [
        (False, (255, 255, 255)),
        (True, (0, 51, 113)),
    ]
)
def test_render_form(with_forms, exp_color):
    
    pdf = pdfium.PdfDocument(TestFiles.form)
    if with_forms:
        pdf.init_forms()
    
    if with_forms:
        assert isinstance(pdf.formenv, pdfium.PdfFormEnv)
    else:
        assert pdf.formenv is None
    
    page = pdf[0]
    image = page.render(
        may_draw_forms = with_forms,
    ).to_pil()
    
    assert image.getpixel( (190, 190) ) == exp_color
    assert image.getpixel( (190, 430) ) == exp_color
    assert image.getpixel( (190, 480) ) == exp_color


def test_numpy_nocopy(sample_page):
    bitmap = sample_page.render(scale=0.1)
    array = bitmap.to_numpy()
    assert (bitmap.width, bitmap.height) == (60, 85)
    val_a, val_b = 255, 123
    assert array[0][0][0] == val_a
    bitmap.buffer[0] = val_b
    assert array[0][0][0] == val_b
    array[0][0][0] = val_a
    assert bitmap.buffer[0] == val_a


@pytest.mark.parametrize(
    ("bitmap_format", "rev_byteorder", "is_referenced"),
    [
        (pdfium_c.FPDFBitmap_BGR,  False, False),
        (pdfium_c.FPDFBitmap_BGR,  True,  False),
        (pdfium_c.FPDFBitmap_BGRA, False, False),
        (pdfium_c.FPDFBitmap_BGRA, True,  True),
        (pdfium_c.FPDFBitmap_BGRx, False, False),
        (pdfium_c.FPDFBitmap_BGRx, True,  True),
        (pdfium_c.FPDFBitmap_Gray, False, True),
    ]
)
def test_pil_nocopy_where_possible(bitmap_format, rev_byteorder, is_referenced, sample_page):
    
    bitmap = sample_page.render(
        scale = 0.1,
        rev_byteorder = rev_byteorder,
        force_bitmap_format = bitmap_format,
    )
    pil_image = bitmap.to_pil()
    assert pil_image.size == (60, 85)
    
    val_a, val_b = 255, 123
    if bitmap.n_channels == 4:
        pixel_a = (val_a, 255, 255, 255)
        pixel_b = (val_b, 255, 255, 255)
    elif bitmap.n_channels == 3:
        pixel_a = (val_a, 255, 255)
        pixel_b = (val_b, 255, 255)
    elif bitmap.n_channels == 1:
        pixel_a = val_a
        pixel_b = val_b
    else:
        assert False
    
    assert pil_image.getpixel((0, 0)) == pixel_a
    bitmap.buffer[0] = val_b
    
    if is_referenced:
        
        # changes to the buffer are reflected in the image
        assert pil_image.getpixel((0, 0)) == pixel_b
        
        # changes to the image are reflected in the buffer, since we set `.readonly = False` on after image init
        pil_image.putpixel((0, 0), pixel_a)
        assert pil_image.getpixel((0, 0)) == pixel_a
        assert bitmap.buffer[0] == val_a
        
    else:
        if pil_image.getpixel((0, 0)) == pixel_b:
            warnings.warn(f"PIL now references {bitmap.mode} mode bitmaps.")
        else:
            assert pil_image.getpixel((0, 0)) == pixel_a
