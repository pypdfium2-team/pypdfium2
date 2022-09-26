# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import io
import math
import ctypes
import logging
from os.path import join
from multiprocessing.shared_memory import (
    SharedMemory
)
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
    pil_image = sample_page.render_to(
        pdfium.BitmapConv.pil_image,
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


@pytest.mark.parametrize(
    "rev_byteorder", [False, True]
)
def test_render_page_bgrx(rev_byteorder, sample_page):
    pil_image = sample_page.render_to(
        pdfium.BitmapConv.pil_image,
        prefer_bgrx = True,
        rev_byteorder = rev_byteorder,
    )
    assert pil_image.mode == "RGBX"
    exp_pixels = [(pos, (*value, 255)) for pos, value in ExpRenderPixels]
    _check_pixels(pil_image, exp_pixels)
    pil_image.close()


def test_render_page_alpha(sample_page):
    
    pixels = [
        [(0,   0  ), (0,   0,   0,   0  )],
        [(62,  66 ), (0,   0,   0,   186)],
        [(150, 180), (129, 212, 26,  255)],
        [(150, 390), (42,  96,  153, 255)],
        [(150, 570), (128, 0,   128, 255)],
    ]
    kwargs = dict(
        converter = pdfium.BitmapConv.pil_image,
        fill_colour = (0, 0, 0, 0),
    )
    image = sample_page.render_to(**kwargs)
    image_rev = sample_page.render_to(**kwargs, rev_byteorder=True)
    
    assert image == image_rev
    assert image.mode == "RGBA"
    assert image.size == (595, 842)
    for pos, exp_value in pixels:
        assert image.getpixel(pos) == exp_value
    
    image.save(join(OutputDir, "coloured_alpha.png"))
    for g in (image, image_rev): g.close()


def test_render_page_grey(sample_page):

    kwargs = dict(
        converter = pdfium.BitmapConv.pil_image,
        greyscale = True,
        scale = 0.5,
    )
    image = sample_page.render_to(**kwargs)
    image_rev = sample_page.render_to(**kwargs, rev_byteorder=True)
    assert image == image_rev
    assert image.size == (298, 421)
    assert image.mode == "L"
    image.save(join(OutputDir, "greyscale.png"))
    for g in (image, image_rev): g.close()


@pytest.mark.parametrize(
    "prefer_la", [False, True]
)
def test_render_page_grey_alpha(prefer_la, sample_page):
    converter = pdfium.BitmapConv.pil_image(
        prefer_la = prefer_la,
    )
    image = sample_page.render_to(
        converter,
        greyscale = True,
        fill_colour = (0, 0, 0, 0),
        scale = 0.5,
    )
    assert image.size == (298, 421)
    if prefer_la:
        assert image.mode == "LA"
    else:
        assert image.mode == "RGBA"
    image.save(join(OutputDir, "greyscale_alpha_%s.png" % image.mode))
    image.close()


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
        converter = pdfium.BitmapConv.pil_image,
        fill_colour = fill_colour,
        scale = 0.5,
    )
    image = sample_page.render_to(**kwargs)
    image_rev = sample_page.render_to(**kwargs, rev_byteorder=True)
    assert image == image_rev
    
    bg_pixel = image.getpixel( (0, 0) )
    if fill_colour[3] == 255:
        fill_colour = fill_colour[:-1]
    assert image.size == (298, 421)
    assert bg_pixel == fill_colour
    
    image.close()


def test_render_page_colourscheme():
    
    pdf = pdfium.PdfDocument(TestFiles.text)
    page = pdf.get_page(0)
    colour_scheme = pdfium.ColourScheme(
        path_fill   = (15,  15,  15,  255),
        path_stroke = (255, 255, 255, 255),
        text_fill   = (255, 255, 255, 255),
        text_stroke = (255, 255, 255, 255),
    )
    image = page.render_to(
        pdfium.BitmapConv.pil_image,
        greyscale = True,
        fill_colour = (0, 0, 0, 255),
        colour_scheme = colour_scheme,
    )
    assert image.mode == "L"
    image.save( join(OutputDir, "render_colourscheme.png") )
    
    for g in (page, pdf): g.close()


def test_render_page_custom_allocator(sample_page):
    allocator = lambda n_bytes: (ctypes.c_ubyte * n_bytes)()
    out_array, cl_format, size = sample_page.render_base(allocator=allocator)
    assert len(out_array) == len(cl_format) * size[0] * size[1]
    assert out_array._type_ is ctypes.c_ubyte


@pytest.mark.parametrize(
    "rev_byteorder", [False, True]
)
def test_render_page_tonumpy(rev_byteorder, sample_page):
    
    array, cl_format = sample_page.render_to(
        pdfium.BitmapConv.numpy_ndarray,
        rev_byteorder = rev_byteorder,
    )
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
    
    bytedata, cl_format, size = sample_page.render_to(
        pdfium.BitmapConv.any(bytes),
        scale = 0.5,
        rev_byteorder = rev_byteorder,
    )
    
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
        pil_image = sample_page.render_to(
            pdfium.BitmapConv.pil_image,
            optimise_mode = mode,
            scale = 0.5,
        )
        assert isinstance(pil_image, PIL.Image.Image)
        pil_image.close()


def test_render_page_noantialias(sample_page):
    pil_image = sample_page.render_to(
        pdfium.BitmapConv.pil_image,
        no_smoothtext  = True,
        no_smoothimage = True,
        no_smoothpath  = True,
        scale = 0.5,
    )
    assert isinstance(pil_image, PIL.Image.Image)
    pil_image.close()


def _resolve_shared_mem(mem_name):
    assert isinstance(mem_name, str)
    return SharedMemory(name=mem_name, create=False)


def test_render_page_sharedmem(sample_page):
    shared_mem, cl_format, size = sample_page.render_to(
        converter = pdfium.BitmapConv.any(_resolve_shared_mem),
        use_shared_memory = True,
        rev_byteorder = True,
    )
    
    assert cl_format == "RGB"
    assert size == (595, 842)
    
    # PIL doesn't take memoryview directly, so get a ctypes array representation
    n_bytes = size[0] * size[1] * len(cl_format)
    buffer = (ctypes.c_ubyte * n_bytes).from_buffer(shared_mem.buf)
    
    assert len(shared_mem.buf) >= n_bytes
    assert len(buffer) == n_bytes
    
    pil_image = PIL.Image.frombuffer(cl_format, size, buffer, "raw", cl_format, 0, 1)
    pil_image.save( join(OutputDir, "render_page_sharedmem.png") )
    pil_image.close()
    
    del buffer  # can't close otherwise - FIXME wonky?
    shared_mem.unlink()
    shared_mem.close()


def test_render_pages_no_concurrency(multipage_doc):
    for page in multipage_doc:
        image = page.render_to(
            pdfium.BitmapConv.pil_image,
            scale = 0.5,
            greyscale = True,
        )
        assert isinstance(image, PIL.Image.Image)
        image.close()
        page.close()


@pytest.fixture
def render_pdffile_topil(multipage_doc):
    
    renderer = multipage_doc.render_to(
        pdfium.BitmapConv.pil_image,
        scale = 0.5,
    )
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
    
    renderer = multipage_doc.render_to(
        pdfium.BitmapConv.any(bytes),
        scale = 0.5,
    )
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
    
    renderer = multipage_doc.render_to(
        pdfium.BitmapConv.numpy_ndarray,
        scale = 0.5,
        rev_byteorder = True,
    )
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
        renderer = pdf.render_to(pdfium.BitmapConv.pil_image)
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
        renderer = pdf.render_to(
            pdfium.BitmapConv.pil_image,
            scale = 0.5,
        )
        for image in renderer:
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
    renderer = pdf.render_to(
        pdfium.BitmapConv.pil_image,
        scale = 0.5,
    )
    for image in renderer:
        assert isinstance(image, PIL.Image.Image)
    assert isinstance(pdf._rendering_input, bytes)
    
    pdf.close()


def test_render_pdffile_asbuffer():
    
    pdf = pdfium.PdfDocument(TestFiles.render, file_access=pdfium.FileAccess.BUFFER)
    
    assert pdf._orig_input == TestFiles.render
    assert isinstance(pdf._actual_input, io.BufferedReader)
    assert pdf._rendering_input is None
    assert pdf._file_access is pdfium.FileAccess.BUFFER
    
    renderer = pdf.render_to(
        pdfium.BitmapConv.pil_image,
        scale = 0.5,
    )
    for image in renderer:
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
    
    renderer = pdf.render_to(
        pdfium.BitmapConv.pil_image,
        scale = 0.5,
    )
    for image in renderer:
        assert isinstance(image, PIL.Image.Image)
    assert pdf._rendering_input == TestFiles.render
    
    pdf.close()
