# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import math
import ctypes
import weakref
import logging
from ctypes import c_float
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.misc import (
    OptimiseMode,
    PdfiumError,
    get_functype,
    colour_tohex,
    RotationToConst,
    RotationToDegrees,
    BitmapTypeToStr,
    BitmapTypeToStrReverse,
)
from pypdfium2._helpers.pageobject import (
    PdfPageObject,
)
from pypdfium2._helpers.converters import (
    BitmapConvBase,
    BitmapConvAliases,
)
from pypdfium2._helpers.textpage import PdfTextPage

try:
    import uharfbuzz as harfbuzz
except ImportError:
    harfbuzz = None

logger = logging.getLogger(__name__)


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
        # if the form env of the parent document is initialised, we could call FORM_OnAfterLoadPage() here
        self._finalizer = weakref.finalize(
            self, self._static_close,
            self.raw, self.pdf,
        )
    
    def _tree_closed(self):
        if self.raw is None:
            return True
        return self.pdf._tree_closed()
    
    @staticmethod
    def _static_close(raw, parent):
        # logger.debug("Closing page")
        if parent._tree_closed():
            logger.critical("Document closed before page (this is illegal). Document: %s" % parent)
        # if the form env of the parent document is initialised, we could call FORM_OnBeforeClosePage() here
        pdfium.FPDF_ClosePage(raw)
    
    def close(self):
        """
        Free memory by applying the finalizer for the underlying PDFium page.
        Please refer to the generic note on ``close()`` methods for details.
        """
        if self.raw is None:
            logger.warning("Duplicate close call suppressed on page %s" % self)
            return
        self._finalizer()
        self.raw = None
    
    
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
        success = box_func(self.raw, left, bottom, right, top)
        if not success:
            # TODO avoid repeated initialisation of c_float objects for fallback
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
    
    
    def insert_object(self, pageobj):
        """
        Insert a page object into the page.
        
        Position and form are defined by the object's matrix.
        If it is the identity matrix, the object will appear as-is on the bottom left corner of the page.
        
        The page object must not belong to a page yet. If it belongs to a PDF, this page must be part of the PDF.
        
        You may want to call :meth:`.generate_content` once you finished adding new content to the page.
        
        Parameters:
            pageobj (PdfPageObject): The page object to insert.
        """
        
        if pageobj.page is not None:
            raise ValueError("The pageobject you attempted to insert already belongs to a page.")
        if (pageobj.pdf is not None) and (pageobj.pdf is not self.pdf):
            raise ValueError("The pageobject you attempted to insert belongs to a different PDF.")
        
        pdfium.FPDFPage_InsertObject(self.raw, pageobj.raw)
        
        pageobj.page = self
        pageobj.pdf = self.pdf
    
    
    def generate_content(self):
        """
        Generate added page content.
        This function shall be called to apply changes before saving the document or reloading the page.
        """
        success = pdfium.FPDFPage_GenerateContent(self.raw)
        if not success:
            raise PdfiumError("Generating page content failed.")
    
    
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
        *Requires* :mod:`uharfbuzz`
        
        Insert text into the page at a specified position, using the writing system's ligature.
        This function supports Asian scripts such as Hindi.
        
        You may want to call :meth:`.generate_content` once you finished adding new content to the page.
        
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
        
        # User-contributed code
        # SPDX-FileCopyrightText: 2022 Anurag Bansal <anurag.bansal.585@gmail.com>
        
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
            
            type = pdfium.FPDFPageObj_GetType(raw_obj)
            yield PdfPageObject(
                raw = raw_obj,
                type = type,
                page = self,
                pdf = self.pdf,
                level = level,
            )
            
            if level < max_depth-1 and type == pdfium.FPDF_PAGEOBJ_FORM:
                yield from self.get_objects(
                    max_depth = max_depth,
                    form = raw_obj,
                    level = level + 1,
                )
    
    
    def render_to(self, converter, **renderer_kws):
        """
        Rasterise a page to a specific output format.
        
        Parameters:
            converter (BitmapConvBase | typing.Callable):
                A translator to convert the output of :meth:`.render_base`. See :class:`.BitmapConv` for a set of built-in converters.
            renderer_kws (dict):
                Keyword arguments to the renderer.
        
        Returns:
            typing.Any: Converter-specific result.
        
        Examples:
            
            .. code-block:: python
                
                # convert to a NumPy array
                array, cl_format = render_to(BitmapConv.numpy_ndarray, ...)
                # passing an initialised converter without arguments is equivalent
                array, cl_format = render_to(BitmapConv.numpy_ndarray(), ...)
                
                # convert to a PIL image (with default settings)
                image = render_to(BitmapConv.pil_image, ...)
                
                # convert to PIL image (with specific settings)
                image = render_to(BitmapConv.pil_image(prefer_la=True), ...)
                
                # convert to bytes using the special "any" converter factory
                data, cl_format, size = render_to(BitmapConv.any(bytes), ...)
        """
        
        args = (self.render_base(**renderer_kws), renderer_kws)
        if isinstance(converter, BitmapConvBase):
            return converter.run(*args, *converter.args, **converter.kwargs)
        elif isinstance(converter, type) and issubclass(converter, BitmapConvBase):
            return converter().run(*args)
        elif callable(converter):
            return converter(*args)
        else:
            raise ValueError("Converter must be an instance or subclass of BitmapConvBase, or a callable, but %s was given." % converter)
    
    
    def render_base(
            self,
            scale = 1,
            rotation = 0,
            crop = (0, 0, 0, 0),
            greyscale = False,
            fill_colour = (255, 255, 255, 255),
            colour_scheme = None,
            optimise_mode = OptimiseMode.NONE,
            draw_annots = True,
            draw_forms = True,
            no_smoothtext = False,
            no_smoothimage = False,
            no_smoothpath = False,
            force_halftone = False,
            limit_image_cache = False,
            rev_byteorder = False,
            prefer_bgrx = False,
            force_bitmap_format = None,
            extra_flags = 0,
            allocator = None,
            memory_limit = 2**30,
        ):
        """
        Rasterise the page to a :class:`ctypes.c_ubyte` array. This is the base method for :meth:`.render_to`.
        
        Parameters:
            
            scale (float):
                A factor scaling the number of pixels that represent the length of 1 PDF canvas unit (usually 1/72 in). [1]_
                This defines the resolution of the image. To convert a DPI value to a scale factor, multiply it by the size of 1 canvas unit in inches.
                
                .. [1] Since PDF 1.6, pages may define a so-called user unit. In this case, 1 canvas unit is equivalent to ``user_unit * (1/72)`` inches. pypdfium2 currently does not take this into account.
                
            rotation (int):
                A rotation value in degrees (0, 90, 180, or 270), in addition to page rotation.
            
            crop (typing.Tuple[float, float, float, float]):
                Amount in PDF canvas units to cut off from page borders (left, bottom, right, top).
                Crop is applied after rotation.
            
            greyscale (bool):
                Whether to render in greyscale mode (no colours).
            
            fill_colour (typing.Tuple[int, int, int, int]):
                Colour the bitmap will be filled with before rendering.
                Shall be a list of values for red, green, blue and alpha, ranging from 0 to 255.
                For RGB, 0 will include nothing of the colour in question, while 255 will fully include it.
                For Alpha, 0 means full transparency, while 255 means no transparency.
            
            colour_scheme (ColourScheme | None):
                A custom colour scheme for rendering, defining fill and stroke colours for path and text objects.
            
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
            
            limit_image_cache (bool):
                Limit image cache size.
            
            rev_byteorder (bool):
                By default, the output pixel format will be ``BGR(A/X)``.
                This option may be used to render with reversed byte order, leading to ``RGB(A/X)`` output instead.
                ``L`` is unaffected.
            
            prefer_bgrx (bool):
                Request the use of a four-channel pixel format for coloured output, even if rendering without transparency.
                (i. e. ``BGRX``/``RGBX`` rather than ``BGR``/``RGB``).
            
            force_bitmap_format (int | None):
                If given, override the automatic pixel format selection and enforce the use of a specific format.
                May be one of the :attr:`FPDFBitmap_*` constants, except :attr:`FPDFBitmap_Unknown`.
                For instance, this may be used to render in greyscale mode while using ``BGR`` as output format (default choice would be ``L``).
            
            extra_flags (int):
                Additional PDFium rendering flags. Multiple flags may be combined with bitwise OR (``|`` operator).
            
            allocator (typing.Callable | None):
                A function to provide a custom ctypes buffer. It is called with the required buffer size in bytes.
                If not given, a new :class:`ctypes.c_ubyte` array is allocated by Python (this simplify memory management, as opposed to allocation by PDFium).
            
            memory_limit (int | None):
                Maximum number of bytes that may be allocated (defaults to 1 GiB rsp. 2^30 bytes).
                If the limit would be exceeded, a :exc:`RuntimeError` is raised.
                If :data:`None` or 0, this function may allocate arbitrary amounts of memory as far as Python and the OS permit.
            
        Returns:
            (ctypes array, str, (int, int)): Bitmap data, colour format, and image size.
            The colour format may be ``BGR``/``RGB``, ``BGRA``/``RGBA``, ``BGRX``/``RGBX``, or ``L``, depending on the parameters *colour*, *greyscale*, *rev_byteorder* and *prefer_bgrx*.
            Image size is given in pixels as a tuple of width and height.
        """
        
        if force_bitmap_format in (None, pdfium.FPDFBitmap_Unknown):
            cl_pdfium = _auto_bitmap_format(fill_colour, greyscale, prefer_bgrx)
        else:
            cl_pdfium = force_bitmap_format
        
        if cl_pdfium == pdfium.FPDFBitmap_Gray:
            rev_byteorder = False
        
        if rev_byteorder:
            cl_string = BitmapTypeToStrReverse[cl_pdfium]
        else:
            cl_string = BitmapTypeToStr[cl_pdfium]
        
        c_fill_colour = colour_tohex(fill_colour, rev_byteorder)
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
            if ctypes.sizeof(buffer) < n_bytes:
                raise RuntimeError("Not enough bytes allocated (buffer length: %s, required bytes: %s)." % (ctypes.sizeof(buffer), n_bytes))
        
        bitmap = pdfium.FPDFBitmap_CreateEx(width, height, cl_pdfium, buffer, stride)
        pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, c_fill_colour)
        
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
        if limit_image_cache:
            render_flags |= pdfium.FPDF_RENDER_LIMITEDIMAGECACHE
        if rev_byteorder:
            render_flags |= pdfium.FPDF_REVERSE_BYTE_ORDER
        if colour_scheme and colour_scheme.fill_to_stroke:
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
        
        if colour_scheme is None:
            pdfium.FPDF_RenderPageBitmap(*render_args)
        else:
            
            ifsdk_pause = pdfium.IFSDK_PAUSE()
            ifsdk_pause.version = 1
            ifsdk_pause.NeedToPauseNow = get_functype(pdfium.IFSDK_PAUSE, "NeedToPauseNow")(lambda _: False)
            
            fpdf_cs = colour_scheme.convert(rev_byteorder)
            status = pdfium.FPDF_RenderPageBitmapWithColorScheme_Start(*render_args, fpdf_cs, ifsdk_pause)
            
            assert status == pdfium.FPDF_RENDER_DONE
            pdfium.FPDF_RenderPage_Close(self.raw)
        
        if draw_forms:
            form_type = pdfium.FPDF_GetFormType(self.pdf.raw)  # consider moving to document ?
            if form_type != pdfium.FORMTYPE_NONE:
                form_env = self.pdf.init_formenv()
                pdfium.FPDF_FFLDraw(form_env, *render_args)
        
        return buffer, cl_string, (width, height)


def _auto_bitmap_format(fill_colour, greyscale, prefer_bgrx):
    # no need to take alpha values of colour_scheme into account (drawings are additive)
    if (fill_colour[3] < 255):
        return pdfium.FPDFBitmap_BGRA
    elif greyscale:
        return pdfium.FPDFBitmap_Gray
    elif prefer_bgrx:
        return pdfium.FPDFBitmap_BGRx
    else:
        return pdfium.FPDFBitmap_BGR


class ColourScheme:
    """
    Rendering colour scheme.
    Each colour shall be provided as a list of values for red, green, blue and alpha, ranging from 0 to 255.
    """
    
    def __init__(
            self,
            path_fill,
            path_stroke,
            text_fill,
            text_stroke,
            fill_to_stroke = False,
        ):
        self.colours = dict(
            path_fill_color = path_fill,
            path_stroke_color = path_stroke,
            text_fill_color = text_fill,
            text_stroke_color = text_stroke,
        )
        self.fill_to_stroke = fill_to_stroke
    
    def convert(self, rev_byteorder):
        """
        Returns:
            The colour scheme as :class:`FPDF_COLORSCHEME` object.
        """
        fpdf_cs = pdfium.FPDF_COLORSCHEME()
        for key, value in self.colours.items():
            setattr(fpdf_cs, key, colour_tohex(value, rev_byteorder))
        return fpdf_cs
