# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-FileCopyrightText: 2022 Anurag Bansal <anurag.bansal.585@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import math
import ctypes
from ctypes import c_float
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.textpage import PdfTextPage
from pypdfium2._helpers._utils import (
    colour_helper,
    BitmapFormatToStr,
    BitmapFormatToStrReverse,
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
            pdf_textobj = pdfium.FPDFPageObj_CreateTextObj(self._pdf.raw, pdf_font.raw, font_size)
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
            colour = (255, 255, 255, 255),
            greyscale = False,
            optimise_mode = OptimiseMode.NONE,
            draw_annots = True,
            draw_forms = True,
            no_smoothtext = False,
            no_smoothimage = False,
            no_smoothpath = False,
            rev_byteorder = False,
            extra_flags = 0,
            memory_limit = 2 ** 30,
        ):
        """
        Rasterise the page to a ctypes ubyte array.
        This is the base function for :func:`.render_tobytes` and :func:`.render_topil`.
        
        Parameters:
            
            scale (float):
                This parameter defines the resolution of the image.
                Technically speaking, it is a factor sacling the number of pixels that represent a length of 1 PDF canvas unit (equivalent to 1/72 of an inch by default). [1]_
                
                .. [1] Since PDF 1.6, pages may define a so-called user unit. In this case, 1 canvas unit is equivalent to ``user_unit * (1/72)`` inches. pypdfium2 currently does not take this into account.
                
            rotation (int):
                A rotation value in degrees (0, 90, 180, or 270), in addition to page rotation.
            
            crop (typing.Tuple[float, float, float, float]):
                Amount in PDF canvas units to cut off from page borders (left, bottom, right, top).
                Crop is applied after rotation.
            
            colour (typing.Tuple[int, int, int, int]):
                Page background colour. Shall be a list of values for red, green, blue and alpha, ranging from 0 to 255.
                For RGB, 0 will include nothing of the colour in question, while 255 will fully include it.
                For Alpha, 0 means full transparency, while 255 means no transparency.
            
            greyscale (bool):
                Whether to render in greyscale mode (no colours).
            
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
            
            rev_byteorder (bool):
                By default, the output pixel format will be ``BGR(A)``.
                This option may be used to render with reversed byte order, leading to ``RGB(A)`` output instead.
                ``L`` is unaffected.
            
            extra_flags (int):
                Additional PDFium rendering flags. Multiple flags may be combined with binary OR.
            
            memory_limit (int | None):
                Maximum number of bytes that may be allocated (defaults to 1 GiB rsp. 2^30 bytes).
                If the limit is exceeded, a :exc:`RuntimeError` will be raised.
                If :data:`None` or 0, this function may allocate arbitrary amounts of memory as far as Python and the OS permit.
            
        Returns:
            (``ctypes.c_ubyte_Array_%d``, str, (int, int)):
            Ctypes array, colour format, and image size.
            The colour format may be ``BGR``/``RGB``, ``BGRA``/``RGBA``, or ``L``, depending on the parameters *colour*, *greyscale* and *rev_byteorder*.
            Image size is given in pixels as a tuple of width and height.
        
        Hint:
            To convert a DPI value to a scale factor, divide it by 72.
        Note:
            The ctypes array is allocated by Python (not PDFium), so we don't need to care about freeing memory.
        """
        
        c_colour, cl_pdfium, rev_byteorder = colour_helper(*colour, greyscale, rev_byteorder)
        
        if rev_byteorder:
            cl_string = BitmapFormatToStrReverse[cl_pdfium]
        else:
            cl_string = BitmapFormatToStr[cl_pdfium]
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
        
        stride = width * n_channels  # number of bytes per row
        n_bytes = stride * height    # total number of bytes
        if memory_limit and n_bytes > memory_limit:
            raise RuntimeError(
                "Planned allocation of %s bytes exceeds the defined limit of %s. " % (n_bytes, memory_limit) +
                "Consider adjusting the *memory_limit* parameter."
            )
        
        buffer = (ctypes.c_ubyte * n_bytes)()
        bitmap = pdfium.FPDFBitmap_CreateEx(width, height, cl_pdfium, buffer, stride)
        if colour[3] > 0:
            pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, c_colour)
        
        render_flags = 0
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
        if rev_byteorder:
            render_flags |= pdfium.FPDF_REVERSE_BYTE_ORDER
        
        if optimise_mode is OptimiseMode.NONE:
            pass
        elif optimise_mode is OptimiseMode.LCD_DISPLAY:
            render_flags |= pdfium.FPDF_LCD_TEXT
        elif optimise_mode is OptimiseMode.PRINTING:
            render_flags |= pdfium.FPDF_PRINTING
        else:
            raise ValueError("Invalid optimise_mode %s" % optimise_mode)
        
        render_flags |= extra_flags
        
        render_args = (bitmap, self._page, -crop[0], -crop[3], src_width, src_height, RotationToConst[rotation], render_flags)
        pdfium.FPDF_RenderPageBitmap(*render_args)
        
        if draw_forms:
            form_fill = pdfium.FPDFDOC_InitFormFillEnvironment(self.pdf.raw, pdfium.FPDF_FORMFILLINFO(2))
            pdfium.FPDF_FFLDraw(form_fill, *render_args)
            pdfium.FPDFDOC_ExitFormFillEnvironment(form_fill)
        
        return buffer, cl_string, (width, height)
    
    
    def render_tobytes(self, *args, **kwargs):
        """
        Rasterise the page to bytes. Parameters are the same as for :meth:`.render_base`.
        
        Returns:
            (bytes, str, (int, int)): Image data, colour format, and size.
        """
        c_array, cl_format, size = self.render_base(*args, **kwargs)
        return bytes(c_array), cl_format, size
    
    
    def render_topil(self, *args, **kwargs):
        """
        *Requires* :mod:`PIL`.
        
        Rasterise the page to a PIL image. Parameters are the same as for :meth:`.render_base`.
        
        Returns:
            PIL.Image.Image: An image of the page.
        """
        
        if not have_pil:
            raise RuntimeError("Pillow library needs to be installed for render_topil().")
        
        c_array, cl_src, size = self.render_base(*args, **kwargs)
        
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
            int: The type of the object (``FPDF_PAGEOBJ_...``).
        """
        return pdfium.FPDFPageObj_GetType(self._pageobj)
