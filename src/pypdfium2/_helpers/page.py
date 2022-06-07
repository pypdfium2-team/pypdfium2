# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-FileCopyrightText: 2022 Anurag Bansal <anurag.bansal.585@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import math
import ctypes
from ctypes import c_float, byref
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.textpage import PdfTextPage
from pypdfium2._helpers._utils import (
    colour_tohex,
    get_colourformat,
    ColourMapping,
    RotationToConst,
    RotationToDegrees,
)
from pypdfium2._helpers.misc import (
    raise_error,
    OptimiseMode,
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
        ret_code = box_func(self._page, byref(left), byref(bottom), byref(right), byref(top))
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
            raise_error("Loading the text page failed")
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
            annotations = True,
            greyscale = False,
            optimise_mode = OptimiseMode.NONE,
            no_antialias = (),
        ):
        """
        Rasterise the page to a ctypes ubyte array.
        This is the base function for :func:`.render_tobytes` and :func:`.render_topil`.
        
        Parameters:
            
            scale (float):
                Define the quality (or size) of the image.
                By default, one PDF point (1/72in) is rendered to 1x1 pixel. This factor scales the number of pixels that represent one point.
                Higher values increase quality, file size and rendering duration, while lower values reduce them.
                Note that UserUnit is not taken into account, so if you are using pypdfium2 in conjunction with an other PDF library, you may want to check for a possible ``/UserUnit`` in the page dictionary and multiply this scale factor with it.
            
            rotation (int):
                A rotation value in degrees (0, 90, 180, or 270), in addition to page rotation.
            
            crop (typing.Tuple[float, float, float, float]):
                Amount in PDF canvas units to cut off from page borders (left, bottom, right, top).
                Crop is applied after rotation.
            
            colour (typing.Optional[ typing.Tuple[int, int, int, typing.Optional[int]] ]):
                Page background colour. Defaults to white.
                It can either be :data:`None`, or values of red, green, blue, and alpha ranging from 0 to 255.
                If :data:`None`, the bitmap will not be filled with a colour, resulting in transparent background.
                For RGB, 0 will include nothing of the colour in question, while 255 will completely include it. For Alpha, 0 means full transparency, while 255 means no transparency.
            
            annotations (bool):
                Whether to render page annotations.
            
            greyscale (bool):
                Whether to render in greyscale mode (no colours).
            
            optimise_mode (OptimiseMode):
                How to optimise page rendering.
            
            no_antialias (typing.Sequence[str]):
                A list of item types that shall not be smoothed (text, image, path).
        
        Returns:
            (BitmapDataHolder, str, (int, int)):
            Bitmap data holder, colour format, and image size.
            The colour format can be ``BGRA``, ``BGR``, or ``L``, depending on the parameters *colour* and *greyscale*.
            Image size is given in pixels as a tuple of width and height.
        """
        
        if colour is None:
            fpdf_colour, use_alpha = None, True
        else:
            fpdf_colour, use_alpha = colour_tohex(*colour)
        
        cl_format, cl_pdfium = get_colourformat(use_alpha, greyscale)
        n_colours = len(cl_format)
        
        form_config = pdfium.FPDF_FORMFILLINFO(2)
        form_fill = pdfium.FPDFDOC_InitFormFillEnvironment(self._pdf.raw, form_config)
        
        src_width  = math.ceil(self.get_width()  * scale)
        src_height = math.ceil(self.get_height() * scale)
        if rotation in (90, 270):
            src_width, src_height = src_height, src_width
        
        crop = [math.ceil(c*scale) for c in crop]
        width  = src_width  - crop[0] - crop[2]
        height = src_height - crop[1] - crop[3]
        if any(d < 1 for d in (width, height)):
            raise ValueError("Crop exceeds page dimensions (in px): width %s, height %s, crop %s" % (src_width, src_height, crop))
        
        bitmap = pdfium.FPDFBitmap_CreateEx(width, height, cl_pdfium, None, width*n_colours)
        if fpdf_colour is not None:
            pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, fpdf_colour)
        
        render_flags = 0
        
        if annotations:
            render_flags |= pdfium.FPDF_ANNOT
        if greyscale:
            render_flags |= pdfium.FPDF_GRAYSCALE
        
        if "text" in no_antialias:
            render_flags |= pdfium.FPDF_RENDER_NO_SMOOTHTEXT
        if "image" in no_antialias:
            render_flags |= pdfium.FPDF_RENDER_NO_SMOOTHIMAGE
        if "path" in no_antialias:
            render_flags |= pdfium.FPDF_RENDER_NO_SMOOTHPATH
        
        if optimise_mode is OptimiseMode.NONE:
            pass
        elif optimise_mode is OptimiseMode.LCD_DISPLAY:
            render_flags |= pdfium.FPDF_LCD_TEXT
        elif optimise_mode is OptimiseMode.PRINTING:
            render_flags |= pdfium.FPDF_PRINTING
        else:
            raise ValueError("Invalid optimise_mode %s" % optimise_mode)
        
        render_args = (bitmap, self._page, -crop[0], -crop[3], src_width, src_height, RotationToConst[rotation], render_flags)
        pdfium.FPDF_RenderPageBitmap(*render_args)
        pdfium.FPDF_FFLDraw(form_fill, *render_args)
        
        cbuf_ptr = pdfium.FPDFBitmap_GetBuffer(bitmap)
        cbuf_array_ptr = ctypes.cast(cbuf_ptr, ctypes.POINTER(ctypes.c_ubyte * (width*height*n_colours)))
        data_holder = BitmapDataHolder(bitmap, cbuf_array_ptr)
        
        pdfium.FPDFDOC_ExitFormFillEnvironment(form_fill)
        
        return data_holder, cl_format, (width, height)
    
    
    def render_tobytes(self, *args, **kwargs):
        """
        Rasterise the page to bytes. Parameters are the same as for :meth:`.render_base`.
        
        Returns:
            (bytes, str, (int, int)): Image data, colour format, and size.
        """
        
        data_holder, cl_format, size = self.render_base(*args, **kwargs)
        data = bytes( data_holder.get_data() )
        data_holder.close()
        
        return data, cl_format, size
    
    
    def render_topil(self, *args, **kwargs):
        """
        *Requires* :mod:`PIL`.
        
        Rasterise the page to a PIL image. Parameters are the same as for :meth:`.render_base`.
        
        Returns:
            PIL.Image.Image: An image of the page.
        """
        
        if not have_pil:
            raise RuntimeError("Pillow library needs to be installed for render_topil().")
        
        data_holder, cl_format, size = self.render_base(*args, **kwargs)
        pil_image = PIL.Image.frombytes(ColourMapping[cl_format], size, data_holder.get_data(), "raw", cl_format, 0, 1)
        data_holder.close()
        
        return pil_image


class BitmapDataHolder:
    
    def __init__(self, bm_handle, bm_array_ptr):
        self.bm_handle = bm_handle
        self.bm_array_ptr = bm_array_ptr
    
    def get_data(self):
        return self.bm_array_ptr.contents
    
    def close(self):
        pdfium.FPDFBitmap_Destroy(self.bm_handle)


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
        ret_code = pdfium.FPDFPageObj_GetBounds(self._pageobj, byref(left), byref(bottom), byref(right), byref(top))
        if not ret_code:
            raise_error("Locating the page object failed")
        return (left.value, bottom.value, right.value, top.value)
    
    def get_type(self):
        """
        Returns:
            int: The type of the object (``FPDF_PAGEOBJ_...``).
        """
        return pdfium.FPDFPageObj_GetType(self._pageobj)
