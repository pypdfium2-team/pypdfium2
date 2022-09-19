# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-FileCopyrightText: 2022 Anurag Bansal <anurag.bansal.585@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import math
import ctypes
from ctypes import c_float
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers._utils import (
    get_functype,
    validate_colors,
    color_tohex,
    get_bitmap_format,
    RotationToConst,
    RotationToDegrees,
)
from pypdfium2._helpers.misc import (
    OptimiseMode,
    PdfiumError,
)
from pypdfium2._helpers.converters import BitmapConvAliases
from pypdfium2._helpers.textpage import PdfTextPage

try:
    import uharfbuzz as harfbuzz
except ImportError:
    harfbuzz = None


class PdfPage (BitmapConvAliases):
    """
    Page helper class.
    
    Attributes:
        raw (FPDF_PAGE): The underlying PDFium page handle.
        pdf (PdfDocument): Reference to the document this page belongs to.
    """
    
    def __init__(self, raw, pdf):
        self.raw = raw
        self.pdf = pdf
    
    def close(self):
        """
        Close the page to release allocated memory.
        This function shall be called when finished working with the object.
        """
        pdfium.FPDF_ClosePage(self.raw)
    
    
    def get_width(self):
        """
        Returns:
            float: Page width (horizontal size).
        """
        return pdfium.FPDF_GetPageWidthF(self.raw)
    
    def get_height(self):
        """
        Returns:
            float: Page height (vertical size).
        """
        return pdfium.FPDF_GetPageHeightF(self.raw)
    
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
        return RotationToDegrees[ pdfium.FPDFPage_GetRotation(self.raw) ]
    
    def set_rotation(self, rotation):
        """ Define the absolute, clockwise page rotation (0, 90, 180, or 270 degrees). """
        pdfium.FPDFPage_SetRotation(self.raw, RotationToConst[rotation])
    
    
    def _get_box(self, box_func, fallback_func):
        left, bottom, right, top = c_float(), c_float(), c_float(), c_float()
        ret_code = box_func(self.raw, left, bottom, right, top)
        if not ret_code:
            return fallback_func()
        return (left.value, bottom.value, right.value, top.value)
    
    def _set_box(self, box_func, l, b, r, t):
        if not all(isinstance(val, (int, float)) for val in (l, b, r, t)):
            raise ValueError("Box values must be int or float.")
        box_func(self.raw, l, b, r, t)
    
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
        textpage = pdfium.FPDFText_LoadPage(self.raw)
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
            pdfium.FPDFPage_InsertObject(self.raw, pdf_textobj)
            start_point += (pos.x_advance / hb_font.scale) * font_size
        
        pdfium.FPDFPage_GenerateContent(self.raw)
    
    
    def get_objects(self, max_depth=2, form=None, level=0):
        """
        Iterate through the page objects on this page.
        
        Parameters:
            max_depth (int):
                Maximum recursion depth to consider when descending into Form XObjects.
        
        Yields:
            :class:`.PdfPageObject`: The page object.
        """
        
        if form is None:
            count_objects = pdfium.FPDFPage_CountObjects
            get_object = pdfium.FPDFPage_GetObject
            parent = self.raw
        else:
            count_objects = pdfium.FPDFFormObj_CountObjects
            get_object = pdfium.FPDFFormObj_GetObject
            parent = form
        
        n_objects = count_objects(parent)
        if n_objects == 0:
            return
        elif n_objects < 0:
            raise PdfiumError("Failed to get number of page objects.")
        
        for i in range(n_objects):
            
            raw_obj = get_object(parent, i)
            if raw_obj is None:
                raise PdfiumError("Failed to get page object.")
            
            helper_obj = PdfPageObject(
                raw = raw_obj,
                page = self,
                level = level,
            )
            yield helper_obj
            
            if level < max_depth-1 and helper_obj.type == pdfium.FPDF_PAGEOBJ_FORM:
                yield from self.get_objects(
                    max_depth = max_depth,
                    form = raw_obj,
                    level = level + 1,
                )
    
    
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
            prefer_bgrx = False,
            extra_flags = 0,
            allocator = None,
            memory_limit = 2**30,
        ):
        """
        Rasterise the page to a :class:`ctypes.c_ubyte` array.
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
            
            greyscale (bool):
                Whether to render in greyscale mode (no colors).
            
            color (typing.Tuple[int, int, int, int]):
                Page background color. Shall be a list of values for red, green, blue and alpha, ranging from 0 to 255.
                For RGB, 0 will include nothing of the color in question, while 255 will fully include it.
                For Alpha, 0 means full transparency, while 255 means no transparency.
            
            color_scheme (ColorScheme | None):
                A custom color scheme for rendering, defining fill and stroke colors for path and text objects.
            
            fill_to_stroke (bool):
                Whether fill paths need to be stroked. This option is ignored if *color_scheme* is :data:`None`.
            
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
                Always use halftone for image stretching.
            
            rev_byteorder (bool):
                By default, the output pixel format will be ``BGR(A)``.
                This option may be used to render with reversed byte order, leading to ``RGB(A)`` output instead.
                ``L`` is unaffected.
            
            prefer_bgrx (bool):
                TODO
            
            extra_flags (int):
                Additional PDFium rendering flags. Multiple flags may be combined with binary OR.
                Flags not covered by other options include :data:`FPDF_RENDER_LIMITEDIMAGECACHE` and :data:`FPDF_NO_NATIVETEXT`, for instance.
            
            allocator (typing.Callable | None):
                
                | A function to provide a custom :class:`ctypes.c_ubyte` array. It is called with the required number of bytes (i. e. the length the array shall have).
                | If not given, a new buffer is allocated by ctypes (not PDFium), so Python takes care of all memory management.
                
                | If you wish to render to an existing buffer that was not alloacted by ctypes itself, note that you may get a ctypes array representation of arbitrary memory using ``(ctypes.c_ubyte*n_bytes).from_address(mem_address)``, where *n_bytes* shall be the number of bytes to encompass, and *mem_address* the memory address of the first byte.
                | This may be used to directly write the pixel data to a specific place in memory (e. g. a GUI widget buffer), avoiding unnecessary data copying.
                
                Callers must ensure that ...
                
                * the buffer and its ctypes representation are large enough to hold the requested number of bytes
                * the memory remains valid as long as the ctypes array is used
                * the memory is freed once it is not needed anymore
            
            memory_limit (int | None):
                Maximum number of bytes that may be allocated (defaults to 1 GiB rsp. 2^30 bytes).
                If the limit would be exceeded, a :exc:`RuntimeError` is raised.
                If :data:`None` or 0, this function may allocate arbitrary amounts of memory as far as Python and the OS permit.
            
        Returns:
            (ctypes.c_ubyte array, str, (int, int)):
            Ctypes array, color format, and image size.
            The color format may be ``BGR``/``RGB``, ``BGRA``/``RGBA``, or ``L``, depending on the parameters *color*, *greyscale* and *rev_byteorder*.
            Image size is given in pixels as a tuple of width and height.
        
        Hint:
            To convert a DPI value to a scale factor, divide it by 72.
        """
        
        validate_colors(color, color_scheme)
        cl_pdfium, cl_string, rev_byteorder = get_bitmap_format(color, greyscale, rev_byteorder, prefer_bgrx)
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
        
        if allocator is None:
            buffer = (ctypes.c_ubyte * n_bytes)()
        else:
            buffer = allocator(n_bytes)
            if buffer._type_ is not ctypes.c_ubyte:
                raise RuntimeError("Array must be of type ctypes.c_ubyte. Consider using ctypes.cast().")
            if len(buffer) < n_bytes:
                raise RuntimeError("Not enough bytes allocated (buffer length: %s, required bytes: %s)." % (len(buffer), n_bytes))
        
        bitmap = pdfium.FPDFBitmap_CreateEx(width, height, cl_pdfium, buffer, stride)
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
        
        render_args = (bitmap, self.raw, -crop[0], -crop[3], src_width, src_height, RotationToConst[rotation], render_flags)
        
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
            pdfium.FPDF_RenderPage_Close(self.raw)
        
        if draw_forms:
            form_env = self.pdf.init_formenv()
            pdfium.FPDF_FFLDraw(form_env, *render_args)
        
        return buffer, cl_string, (width, height)
    
    
    def render_to(self, conv, **renderer_kws):
        result = self.render_base(**renderer_kws)
        return conv.func(result, renderer_kws, *conv.args, **conv.kwargs)


class ColorScheme:
    """
    Rendering color scheme.
    Each color shall be provided as a list of values for red, green, blue and alpha, ranging from 0 to 255.
    
    Note:
        Valid fields are extracted dynamically from the :class:`FPDF_COLORSCHEME` structure.
        Unassigned integer fields default to 0, which means transparent.
    
    Parameters:
        path_fill_color
        path_stroke_color
        text_fill_color
        text_stroke_color
    """
    
    def __init__(self, **caller_kws):
        self.kwargs = {k: v for k, v in caller_kws.items() if v is not None}
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
    """
    Page object helper class.
    
    Attributes:
        raw (FPDF_PAGEOBJECT): The underlying PDFium pageobject handle.
        page (PdfPage): Reference to the page this pageobject belongs to.
        level (int): Nesting level signifying the number of parent Form XObjects. Zero if the object is not nested in a Form XObject.
        type (int): The type of the object (:data:`FPDF_PAGEOBJ_...`).
    """
    
    def __init__(self, raw, page, level=0):
        self.raw = raw
        self.page = page
        self.level = level
        self.type = pdfium.FPDFPageObj_GetType(self.raw)
    
    def get_pos(self):
        """
        Get the position of the object on the page.
        
        Returns:
            A tuple of four :class:`float` coordinates for left, bottom, right, and top.
        """
        left, bottom, right, top = c_float(), c_float(), c_float(), c_float()
        ret_code = pdfium.FPDFPageObj_GetBounds(self.raw, left, bottom, right, top)
        if not ret_code:
            raise PdfiumError("Locating the page object failed")
        return (left.value, bottom.value, right.value, top.value)
