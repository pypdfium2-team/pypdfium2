# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import re
import math
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

# TODO bitmap/info testing (share in common function)


@pytest.fixture
def sample_page():
    pdf = pdfium.PdfDocument(TestFiles.render)
    page = pdf.get_page(0)
    yield page


@pytest.fixture
def multipage_doc():
    pdf = pdfium.PdfDocument(TestFiles.multipage)
    yield pdf


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
        pdfium.PdfBitmap.to_pil,
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


@pytest.mark.parametrize(
    "rev_byteorder", [False, True]
)
def test_render_page_bgrx(rev_byteorder, sample_page):
    pil_image = sample_page.render(
        pdfium.PdfBitmap.to_pil,
        prefer_bgrx = True,
        rev_byteorder = rev_byteorder,
    )
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
        converter = pdfium.PdfBitmap.to_pil,
        fill_colour = (0, 0, 0, 0),
    )
    image = sample_page.render(**kwargs)
    image_rev = sample_page.render(**kwargs, rev_byteorder=True)
    
    assert image == image_rev
    assert image.mode == "RGBA"
    assert image.size == (595, 842)
    for pos, exp_value in pixels:
        assert image.getpixel(pos) == exp_value
    
    image.save(join(OutputDir, "coloured_alpha.png"))


def test_render_page_grey(sample_page):
    kwargs = dict(
        converter = pdfium.PdfBitmap.to_pil,
        greyscale = True,
        scale = 0.5,
    )
    image = sample_page.render(**kwargs)
    image_rev = sample_page.render(**kwargs, rev_byteorder=True)
    assert image == image_rev
    assert image.size == (298, 421)
    assert image.mode == "L"
    image.save(join(OutputDir, "greyscale.png"))


@pytest.mark.parametrize(
    "fill_colour",
    [
        (255, 255, 255, 255),
        (60,  70,  80,  100),
        (255, 255, 255, 255),
        (0,   255, 255, 255),
        (255, 0,   255, 255),
        (255, 255, 0,   255),
    ]
)
def test_render_page_fill_colour(fill_colour, sample_page):
    kwargs = dict(
        converter = pdfium.PdfBitmap.to_pil,
        fill_colour = fill_colour,
        scale = 0.5,
    )
    image = sample_page.render(**kwargs)
    image_rev = sample_page.render(**kwargs, rev_byteorder=True)
    assert image == image_rev
    
    bg_pixel = image.getpixel( (0, 0) )
    if fill_colour[3] == 255:
        fill_colour = fill_colour[:-1]
    assert image.size == (298, 421)
    assert bg_pixel == fill_colour


def test_render_page_colourscheme():
    pdf = pdfium.PdfDocument(TestFiles.text)
    page = pdf.get_page(0)
    colour_scheme = pdfium.ColourScheme(
        path_fill   = (15,  15,  15,  255),
        path_stroke = (255, 255, 255, 255),
        text_fill   = (255, 255, 255, 255),
        text_stroke = (255, 255, 255, 255),
    )
    image = page.render(
        pdfium.PdfBitmap.to_pil,
        greyscale = True,
        fill_colour = (0, 0, 0, 255),
        colour_scheme = colour_scheme,
    )
    assert image.mode == "L"
    image.save( join(OutputDir, "render_colourscheme.png") )


@pytest.mark.parametrize(
    "rev_byteorder", [False, True]
)
def test_render_page_tonumpy(rev_byteorder, sample_page):
    
    array, info = sample_page.render(
        pdfium.PdfBitmap.to_numpy,
        rev_byteorder = rev_byteorder,
        pass_info = True,
    )
    assert isinstance(array, numpy.ndarray)
    assert isinstance(info, pdfium.PdfBitmapInfo)
    mode = info.get_mode()
    if rev_byteorder:
        assert mode == "RGB"
    else:
        assert mode == "BGR"
    
    for (x, y), value in ExpRenderPixels:
        if rev_byteorder:
            assert tuple(array[y][x]) == value
        else:
            assert tuple(array[y][x]) == tuple(reversed(value))


def test_render_page_optimisation(sample_page):
    
    modes = get_members(pdfium.OptimiseMode)
    assert len(modes) == 3
    assert set(modes) == set([
        pdfium.OptimiseMode.NONE,
        pdfium.OptimiseMode.LCD_DISPLAY,
        pdfium.OptimiseMode.PRINTING,
    ])
    
    for mode in modes:
        pil_image = sample_page.render(
            pdfium.PdfBitmap.to_pil,
            optimise_mode = mode,
            scale = 0.5,
        )
        assert isinstance(pil_image, PIL.Image.Image)


def test_render_page_noantialias(sample_page):
    pil_image = sample_page.render(
        pdfium.PdfBitmap.to_pil,
        no_smoothtext  = True,
        no_smoothimage = True,
        no_smoothpath  = True,
        scale = 0.5,
    )
    assert isinstance(pil_image, PIL.Image.Image)


def test_render_pages_no_concurrency(multipage_doc):
    for page in multipage_doc:
        image = page.render(
            pdfium.PdfBitmap.to_pil,
            scale = 0.5,
            greyscale = True,
        )
        assert isinstance(image, PIL.Image.Image)


@pytest.fixture
def render_pdffile_topil(multipage_doc):
    
    renderer = multipage_doc.render(
        pdfium.PdfBitmap.to_pil,
        scale = 0.5,
    )
    imgs = []
    
    for image in renderer:
        assert isinstance(image, PIL.Image.Image)
        assert image.mode == "RGB"
        imgs.append(image)
    
    assert len(imgs) == 3
    yield imgs


@pytest.fixture
def render_pdffile_tonumpy(multipage_doc):
    
    renderer = multipage_doc.render(
        pdfium.PdfBitmap.to_numpy,
        scale = 0.5,
        rev_byteorder = True,
        pass_info = True,
    )
    imgs = []
    
    for array, info in renderer:
        mode = info.get_mode()
        assert mode == "RGB"
        assert isinstance(array, numpy.ndarray)
        pil_image = PIL.Image.fromarray(array, mode=mode)
        imgs.append(pil_image)
    
    # for i, img in enumerate(imgs):
    #     img.save(join(OutputDir, "numpy_%s.png" % i))
    
    assert len(imgs) == 3
    yield imgs


def test_render_pdffile(render_pdffile_topil, render_pdffile_tonumpy):
    for a, b in zip(render_pdffile_topil, render_pdffile_tonumpy):
        assert a == b


def test_render_pdf_new():
    
    # two pages to actually reach the process pool and not just the single-page shortcut
    pdf = pdfium.PdfDocument.new()
    page_1 = pdf.new_page(50, 100)
    page_2 = pdf.new_page(50, 100)
    renderer = pdf.render(pdfium.PdfBitmap.to_pil)
    
    with pytest.raises(ValueError, match="Cannot render in parallel without input sources."):
        next(renderer)


def test_render_pdfbuffer():
    
    buffer = open(TestFiles.multipage, "rb")
    pdf = pdfium.PdfDocument(buffer)
    assert pdf._orig_input is buffer
    assert pdf._actual_input is buffer
    
    renderer = pdf.render(pdfium.PdfBitmap.to_pil)
    with pytest.raises(ValueError, match=re.escape("Cannot render in parallel with buffer input.")):
        next(renderer)


def test_render_pdfbytes():
    
    with open(TestFiles.multipage, "rb") as fh:
        data = fh.read()
    
    pdf = pdfium.PdfDocument(data)
    assert pdf._orig_input is data
    assert pdf._actual_input is data
    renderer = pdf.render(
        pdfium.PdfBitmap.to_pil,
        scale = 0.5,
    )
    image = next(renderer)
    assert isinstance(image, PIL.Image.Image)


def test_render_pdffile_asbuffer():
    
    pdf = pdfium.PdfDocument(TestFiles.multipage, file_access=pdfium.FileAccess.BUFFER)
    
    assert pdf._orig_input == TestFiles.multipage
    assert isinstance(pdf._actual_input, io.BufferedReader)
    assert pdf._file_access is pdfium.FileAccess.BUFFER
    
    renderer = pdf.render(
        pdfium.PdfBitmap.to_pil,
        scale = 0.5,
    )
    image = next(renderer)
    assert isinstance(image, PIL.Image.Image)
    
    pdf._finalizer()
    assert pdf._actual_input.closed is True


def test_render_pdffile_asbytes():
    
    pdf = pdfium.PdfDocument(TestFiles.multipage, file_access=pdfium.FileAccess.BYTES)
    
    assert pdf._orig_input == TestFiles.multipage
    assert isinstance(pdf._actual_input, bytes)
    assert pdf._file_access is pdfium.FileAccess.BYTES
    
    renderer = pdf.render(
        pdfium.PdfBitmap.to_pil,
        scale = 0.5,
    )
    image = next(renderer)
    assert isinstance(image, PIL.Image.Image)


@pytest.mark.parametrize(
    ("draw_forms", "exp_colour"),
    [
        (False, (255, 255, 255)),
        (True, (0, 51, 113)),
    ]
)
def test_render_form(draw_forms, exp_colour):
    
    pdf = pdfium.PdfDocument(TestFiles.form)
    assert pdf._form_env is None
    assert pdf._form_config is None
    
    page = pdf.get_page(0)
    image = page.render(
        pdfium.PdfBitmap.to_pil,
        draw_forms = draw_forms,
    )
    
    assert image.getpixel( (190, 190) ) == exp_colour
    assert image.getpixel( (190, 430) ) == exp_colour
    assert image.getpixel( (190, 480) ) == exp_colour
    
    if draw_forms:
        assert not pdf._form_finalizer.alive
    else:
        assert pdf._form_finalizer is None
    
    # TODO test that an existing form env is not closed
    assert pdf._form_env is None
    assert pdf._form_config is None


def test_numpy_nocopy(sample_page):
    bitmap = sample_page.render(scale=0.1)
    info = bitmap.info
    array = bitmap.to_numpy()
    assert (info.width, info.height) == (60, 85)
    val_a, val_b = 255, 123
    assert array[0][0][0] == val_a
    bitmap.buffer[0] = val_b
    assert array[0][0][0] == val_b
    array[0][0][0] = val_a
    assert bitmap.buffer[0] == val_a


@pytest.mark.parametrize(
    ("bitmap_format", "rev_byteorder", "is_referenced"),
    [
        (pdfium.FPDFBitmap_BGR,  False, False),
        (pdfium.FPDFBitmap_BGR,  True,  False),
        (pdfium.FPDFBitmap_BGRA, False, False),
        (pdfium.FPDFBitmap_BGRA, True,  True),
        (pdfium.FPDFBitmap_BGRx, False, False),
        (pdfium.FPDFBitmap_BGRx, True,  True),
        (pdfium.FPDFBitmap_Gray, False, True),
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
    n_channels = bitmap.info.n_channels
    
    val_a, val_b = 255, 123
    if n_channels == 4:
        pixel_a = (val_a, 255, 255, 255)
        pixel_b = (val_b, 255, 255, 255)
    elif n_channels == 3:
        pixel_a = (val_a, 255, 255)
        pixel_b = (val_b, 255, 255)
    elif n_channels == 1:
        pixel_a = val_a
        pixel_b = val_b
    else:
        assert False
    
    assert pil_image.getpixel((0, 0)) == pixel_a
    bitmap.buffer[0] = val_b
    if is_referenced:
        # editing the buffer modifies the PIL image
        assert pil_image.getpixel((0, 0)) == pixel_b
        # but it looks like editing the PIL image does not modify the buffer?
        # pil_image.putpixel((0, 0), pixel_a)
        # assert pil_image.getpixel((0, 0)) == pixel_a
        # assert bitmap.buffer[0] == val_a  # fails
    else:
        assert pil_image.getpixel((0, 0)) == pixel_a
