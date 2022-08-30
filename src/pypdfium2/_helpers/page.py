# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-FileCopyrightText: 2022 Anurag Bansal <anurag.bansal.585@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import math
import ctypes
from ctypes import c_float
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.textpage import PdfTextPage
from pypdfium2._helpers._utils import (
    get_functype,
    color_tohex,
    get_bitmap_format,
    RotationToConst,
    RotationToDegrees,
)
from pypdfium2._helpers.misc import (
    OptimiseMode,
    PdfiumError,
)

try:
    import uharfbuzz as harfbuzz
except ImportError:
    have_harfbuzz = False
else:
    have_harfbuzz = True

try:
    import PIL.Image
except ImportError:
    have_pil = False
else:
    have_pil = True

try:
    import numpy
except ImportError:
    have_numpy = False
else:
    have_numpy = True


class PdfPage:
    """ Page helper class. """
    
    def __init__(self, page, pdf):
        self._page = page
        self._pdf = pdf
    
    @property
    def raw(self):
        """ FPDF_PAGE: The raw PDFium page object handle. """
        return self._page
    
    @property
    def pdf(self):
        """ PdfDocument: The document this page belongs to. """
        return self._pdf
    
    def close(self):
        """
        Close the page to release allocated memory.
        This function shall be called when finished working with the object.
        """
        pdfium.FPDF_ClosePage(self._page)
    
    
    def get_width(self):
        """
        Returns:
            float: Page width (horizontal size).
        """
        return pdfium.FPDF_GetPageWidthF(self._page)
    
    def get_height(self):
        """
        Returns:
            float: Page height (vertical size).
        """
        return pdfium.FPDF_GetPageHeightF(self._page)
    
    def get_size(self):
        """
        Returns:
            (float, float): Page width and height.
        """
        return (self.get_width(), self.get_height())
    
    def get_rotation(self):
        """
        Returns:
            int: Clockwise page rotation in degrees.
        """
        return RotationToDegrees[ pdfium.FPDFPage_GetRotation(self._page) ]
    
    def set_rotation(self, rotation):
        """ Define the absolute, clockwise page rotation (0, 90, 180, or 270 degrees). """
        pdfium.FPDFPage_SetRotation(self._page, RotationToConst[rotation])
    
    
    def _get_box(self, box_func, fallback_func):
        left, bottom, right, top = c_float(), c_float(), c_float(), c_float()
        ret_code = box_func(self._page, left, bottom, right, top)
        if not ret_code:
            return fallback_func()
        return (left.value, bottom.value, right.value, top.value)
    
    def _set_box(self, box_func, l, b, r, t):
        if not all(isinstance(val, (int, float)) for val in (l, b, r, t)):
            raise ValueError("Box values must be int or float.")
        box_func(self._page, l, b, r, t)
    
    def get_mediabox(self):
        """
        Returns:
            (float, float, float, float):
            The page MediaBox in PDF canvas units, consisting of four coordinates (usually x0, y0, x1, y1).
            Falls back to ANSI A (0, 0, 612, 792) in case MediaBox is not defined.
        """
        return self._get_box(pdfium.FPDFPage_GetMediaBox, lambda: (0, 0, 612, 792))
    
    def set_mediabox(self, l, b, r, t):
        """
        Set the page's MediaBox by passing four :class:`float` coordinates (usually x0, y0, x1, y1).
        """
        self._set_box(pdfium.FPDFPage_SetMediaBox, l, b, r, t)
    
    def get_cropbox(self):
        """
        Returns:
            The page's CropBox (If not defined, falls back to MediaBox).
        """
        return self._get_box(pdfium.FPDFPage_GetCropBox, self.get_mediabox)
    
    def set_cropbox(self, l, b, r, t):
        """ Set the page's CropBox. """
        self._set_box(pdfium.FPDFPage_SetCropBox, l, b, r, t)
    
    def get_bleedbox(self):
        """
        Returns:
            The page's BleedBox (If not defined, falls back to CropBox).
        """
        return self._get_box(pdfium.FPDFPage_GetBleedBox, self.get_cropbox)
    
    def set_bleedbox(self, l, b, r, t):
        """ Set the page's BleedBox. """
        self._set_box(pdfium.FPDFPage_SetBleedBox, l, b, r, t)
    
    def get_trimbox(self):
        """
        Returns:
            The page's TrimBox (If not defined, falls back to CropBox).
        """
        return self._get_box(pdfium.FPDFPage_GetTrimBox, self.get_cropbox)
    
    def set_trimbox(self, l, b, r, t):
        """ Set the page's TrimBox. """
        self._set_box(pdfium.FPDFPage_SetTrimBox, l, b, r, t)
    
    def get_artbox(self):
        """
        Returns:
            The page's ArtBox (If not defined, falls back to CropBox).
        """
        return self._get_box(pdfium.FPDFPage_GetArtBox, self.get_cropbox)
    
    def set_artbox(self, l, b, r, t):
        """ Set the page's ArtBox. """
        self._set_box(pdfium.FPDFPage_SetArtBox, l, b, r, t)
    
    
    def get_textpage(self):
        """
        Returns:
            PdfTextPage: The text page that corresponds to this page.
        """
        textpage = pdfium.FPDFText_LoadPage(self._page)
        if not textpage:
            raise PdfiumError("Loading the text page failed")
        return PdfTextPage(textpage, self)
    
    
    def insert_text(
            self,
            text,
            pos_x,
            pos_y,
            font_size,
            hb_font,
            pdf_font,
        ):
        """
        *Requires* uharfbuzz.
        
        Insert text into the page at a specified position, using the writing system's ligature.
        This function supports Asian scripts such as Hindi.
        
        Parameters:
            text (str):
                The message to insert.
            pos_x (float):
                Distance from left border to first character.
            pos_y (float):
                Distance from bottom border to first character.
            font_size (float):
                Font size the text shall have.
            hb_font (HarfbuzzFont):
                Harfbuzz font data.
            pdf_font (PdfFont):
                PDF font data.
        """
        
        hb_buffer = harfbuzz.Buffer()
        hb_buffer.add_str(text)
        hb_buffer.guess_segment_properties()
        hb_features = {"kern": True, "liga": True}
        harfbuzz.shape(hb_font.font, hb_buffer, hb_features)
        
        start_point = pos_x
        for info, pos in zip(hb_buffer.glyph_infos, hb_buffer.glyph_positions):
            pdf_textobj = pdfium.FPDFPageObj_CreateTextObj(self.pdf.raw, pdf_font.raw, font_size)
            pdfium.FPDFText_SetCharcodes(pdf_textobj, ctypes.c_uint32(info.codepoint), 1)
            pdfium.FPDFPageObj_Transform(
                pdf_textobj,
                1, 0, 0, 1,
                start_point - (pos.x_offset / hb_font.scale) * font_size,
                pos_y,
            )
            pdfium.FPDFPage_InsertObject(self._page, pdf_textobj)
            start_point += (pos.x_advance / hb_font.scale) * font_size
        
        pdfium.FPDFPage_GenerateContent(self._page)
    
    
    def count_objects(self):
        """
        Returns:
            int: The number of page objects on this page.
        """
        return pdfium.FPDFPage_CountObjects(self._page)
    
    def get_objects(self):
        """
        Iterate through the page objects on this page.
        
        Yields:
            :class:`.PdfPageObject`: Page object helper.
        """
        for i in range( self.count_objects() ):
            raw_obj = pdfium.FPDFPage_GetObject(self._page, i)
            yield PdfPageObject(raw_obj)
    
    
    def render_base(
            self,
            scale = 1,
            rotation = 0,
            crop = (0, 0, 0, 0),
            greyscale = False,
            color = (255, 255, 255, 255),
            color_scheme = None,
            fill_to_stroke = False,
            optimise_mode = OptimiseMode.NONE,
            draw_annots = True,
            draw_forms = True,
            no_smoothtext = False,
            no_smoothimage = False,
            no_smoothpath = False,
            force_halftone = False,
            rev_byteorder = False,
            extra_flags = 0,
            memory_limit = 2**30,
        ):
        """
        Rasterise the page to a ctypes ubyte array.
        This is the base method for :meth:`.render_tobytes`, :meth:`.render_tonumpy` and :meth:`.render_topil`.
        
        Parameters:
            
            scale (float):
                This parameter defines the resolution of the image.
                Technically speaking, it is a factor scaling the number of pixels that represent the length of 1 PDF canvas unit (equivalent to 1/72 of an inch by default). [1]_
                
                .. [1] Since PDF 1.6, pages may define a so-called user unit. In this case, 1 canvas unit is equivalent to ``user_unit * (1/72)`` inches. pypdfium2 currently does not take this into account.
                
            rotation (int):
                A rotation value in degrees (0, 90, 180, or 270), in addition to page rotation.
            
            crop (typing.Tuple[float, float, float, float]):
                Amount in PDF canvas units to cut off from page borders (left, bottom, right, top).
                Crop is applied after rotation.
            
            color (typing.Tuple[int, int, int, int]):
                Page background color. Shall be a list of values for red, green, blue and alpha, ranging from 0 to 255.
                For RGB, 0 will include nothing of the color in question, while 255 will fully include it.
                For Alpha, 0 means full transparency, while 255 means no transparency.
            
            color_scheme (ColorScheme | None):
                A custom color scheme for rendering, defining fill and stroke colors for path and text objects.
            
            fill_to_stroke (bool):
                Whether fill paths need to be stroked. This option is ignored if *color_scheme* is :data:`None`.
            
            greyscale (bool):
                Whether to render in greyscale mode (no colors).
            
            optimise_mode (OptimiseMode):
                How to optimise page rendering.
            
            draw_annots (bool):
                Whether to render page annotations.
            
            draw_forms (bool):
                Whether to render form fields.
            
            no_smoothtext (bool):
                Disable anti-aliasing of text. Implicitly wipes out :attr:`.OptimiseMode.LCD_DISPLAY`.
            
            no_smoothimage (bool):
                Disable anti-aliasing of images.
            
            no_smoothpath (bool):
                Disable anti-aliasing of paths.
            
            force_halftone (bool):
                Always use halftone for image streching.
            
            rev_byteorder (bool):
                By default, the output pixel format will be ``BGR(A)``.
                This option may be used to render with reversed byte order, leading to ``RGB(A)`` output instead.
                ``L`` is unaffected.
            
            extra_flags (int):
                Additional PDFium rendering flags. Multiple flags may be combined with binary OR.
                Flags not covered by other options include :data:`FPDF_RENDER_LIMITEDIMAGECACHE` and :data:`FPDF_NO_NATIVETEXT`, for instance.
            
            memory_limit (int | None):
                Maximum number of bytes that may be allocated (defaults to 1 GiB rsp. 2^30 bytes).
                If the limit is exceeded, a :exc:`RuntimeError` will be raised.
                If :data:`None` or 0, this function may allocate arbitrary amounts of memory as far as Python and the OS permit.
            
        Returns:
            (ctypes.c_ubyte array, str, (int, int)):
            Ctypes array, color format, and image size.
            The color format may be ``BGR/RGB``, ``BGRA/RGBA``, or ``L``, depending on the parameters *color*, *greyscale* and *rev_byteorder*.
            Image size is given in pixels as a tuple of width and height.
        
        Hint:
            To convert a DPI value to a scale factor, divide it by 72.
        Note:
            The ctypes array is allocated by Python (not PDFium), so we don't need to care about freeing memory.
        """
        
        cl_pdfium, cl_string, rev_byteorder = get_bitmap_format(color, greyscale, rev_byteorder)
        c_color = color_tohex(color, rev_byteorder)
        n_channels = len(cl_string)
        
        src_width  = math.ceil(self.get_width()  * scale)
        src_height = math.ceil(self.get_height() * scale)
        if rotation in (90, 270):
            src_width, src_height = src_height, src_width
        
        crop = [math.ceil(c*scale) for c in crop]
        width  = src_width  - crop[0] - crop[2]
        height = src_height - crop[1] - crop[3]
        if any(d < 1 for d in (width, height)):
            raise ValueError("Crop exceeds page dimensions (in px): width %s, height %s, crop %s" % (src_width, src_height, crop))
        
        stride = width * n_channels
        n_bytes = stride * height
        if memory_limit and n_bytes > memory_limit:
            raise RuntimeError(
                "Planned allocation of %s bytes exceeds the defined limit of %s. " % (n_bytes, memory_limit) +
                "Consider adjusting the *memory_limit* parameter."
            )
        
        buffer = (ctypes.c_ubyte * n_bytes)()
        bitmap = pdfium.FPDFBitmap_CreateEx(width, height, cl_pdfium, buffer, stride)
        if color[3] > 0:
            pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, c_color)
        
        render_flags = extra_flags
        if greyscale:
            render_flags |= pdfium.FPDF_GRAYSCALE
        if draw_annots:
            render_flags |= pdfium.FPDF_ANNOT
        if no_smoothtext:
            render_flags |= pdfium.FPDF_RENDER_NO_SMOOTHTEXT
        if no_smoothimage:
            render_flags |= pdfium.FPDF_RENDER_NO_SMOOTHIMAGE
        if no_smoothpath:
            render_flags |= pdfium.FPDF_RENDER_NO_SMOOTHPATH
        if force_halftone:
            render_flags |= pdfium.FPDF_RENDER_FORCEHALFTONE
        if rev_byteorder:
            render_flags |= pdfium.FPDF_REVERSE_BYTE_ORDER
        if fill_to_stroke and color_scheme is not None:
            render_flags |= pdfium.FPDF_CONVERT_FILL_TO_STROKE
        
        if optimise_mode is OptimiseMode.NONE:
            pass
        elif optimise_mode is OptimiseMode.LCD_DISPLAY:
            render_flags |= pdfium.FPDF_LCD_TEXT
        elif optimise_mode is OptimiseMode.PRINTING:
            render_flags |= pdfium.FPDF_PRINTING
        else:
            raise ValueError("Invalid optimise_mode %s" % optimise_mode)
        
        render_args = (bitmap, self._page, -crop[0], -crop[3], src_width, src_height, RotationToConst[rotation], render_flags)
        
        if color_scheme is None:
            pdfium.FPDF_RenderPageBitmap(*render_args)
        else:
            # rendering with color scheme is only available as async variant at the moment
            
            ifsdk_pause = pdfium.IFSDK_PAUSE()
            ifsdk_pause.version = 1
            ifsdk_pause.NeedToPauseNow = get_functype(pdfium.IFSDK_PAUSE, "NeedToPauseNow")(lambda _: False)
            
            fpdf_colorscheme = color_scheme.convert(rev_byteorder)
            status = pdfium.FPDF_RenderPageBitmapWithColorScheme_Start(*render_args, fpdf_colorscheme, ifsdk_pause)
            
            assert status == pdfium.FPDF_RENDER_DONE
            pdfium.FPDF_RenderPage_Close(self._page)
        
        if draw_forms:
            form_fill = pdfium.FPDFDOC_InitFormFillEnvironment(self.pdf.raw, pdfium.FPDF_FORMFILLINFO(2))
            pdfium.FPDF_FFLDraw(form_fill, *render_args)
            pdfium.FPDFDOC_ExitFormFillEnvironment(form_fill)
        
        return buffer, cl_string, (width, height)
    
    
    def render_tobytes(self, **kwargs):
        """
        Rasterise the page to bytes. Parameters match :meth:`.render_base`.
        
        Returns:
            (bytes, str, (int, int)): Image data, color format, and size.
        """
        c_array, *args = self.render_base(**kwargs)
        return bytes(c_array), *args
    
    
    def render_tonumpy(self, **kwargs):
        """
        *Requires* :mod:`numpy`.
        
        Rasterise the page to a NumPy array. Parameters match :meth:`.render_base`.
        
        Returns:
            (numpy.ndarray, str): NumPy array, and color format.
        """
        
        if not have_numpy:
            raise RuntimeError("NumPy library needs to be installed for render_tonumpy().")
        
        c_array, cl_format, (width, height) = self.render_base(**kwargs)
        np_array = numpy.ndarray(
            shape = (height, width, len(cl_format)),
            dtype = numpy.ubyte,
            buffer = c_array,
        )
        
        return np_array, cl_format
    
    
    def render_topil(self, **kwargs):
        """
        *Requires* :mod:`PIL`.
        
        Rasterise the page to a PIL image. Parameters match :meth:`.render_base`.
        
        Returns:
            PIL.Image.Image: An image of the page.
        """
        
        if not have_pil:
            raise RuntimeError("Pillow library needs to be installed for render_topil().")
        
        c_array, cl_src, size = self.render_base(**kwargs)
        
        cl_mapping = {
            "BGRA": "RGBA",
            "BGR":  "RGB",
        }
        if cl_src in cl_mapping:
            cl_dst = cl_mapping[cl_src]
        else:
            cl_dst = cl_src
        
        pil_image = PIL.Image.frombytes(cl_dst, size, c_array, "raw", cl_src, 0, 1)
        return pil_image


class ColorScheme:
    """
    Rendering color scheme. Each color shall be provided as a list of values for red, green, blue and alpha, ranging from 0 to 255.
    (At least one parameter needs to be given.)
    
    Note:
        Valid fields are dynamically extracted from the :class:`FPDF_COLORSCHEME` structure.
    
    Parameters:
        path_fill_color
        path_stroke_color
        text_fill_color
        text_stroke_color
    """
    
    def __init__(self, **_kws):
        self.kwargs = {k: v for k, v in _kws.items() if v is not None}
        fields = [key for key, _ in pdfium.FPDF_COLORSCHEME._fields_]
        assert len(self.kwargs) > 0
        assert all(k in fields for k in self.kwargs.keys())
    
    def convert(self, rev_byteorder):
        """
        Returns:
            The color scheme as :class:`FPDF_COLORSCHEME` object.
        """
        fpdf_colorscheme = pdfium.FPDF_COLORSCHEME()
        for key, value in self.kwargs.items():
            setattr(fpdf_colorscheme, key, color_tohex(value, rev_byteorder))
        return fpdf_colorscheme


class PdfPageObject:
    """ Page object helper class. """
    
    def __init__(self, pageobj):
        self._pageobj = pageobj
    
    def get_pos(self):
        """
        Get the position of the object on the page.
        
        Returns:
            A tuple of four :class:`float` coordinates for left, bottom, right, and top.
        """
        left, bottom, right, top = c_float(), c_float(), c_float(), c_float()
        ret_code = pdfium.FPDFPageObj_GetBounds(self._pageobj, left, bottom, right, top)
        if not ret_code:
            raise PdfiumError("Locating the page object failed")
        return (left.value, bottom.value, right.value, top.value)
    
    def get_type(self):
        """
        Returns:
            int: The type of the object (:data:`FPDF_PAGEOBJ_...`).
        """
        return pdfium.FPDFPageObj_GetType(self._pageobj)
