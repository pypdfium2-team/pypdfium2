# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PdfPage", "PdfColorScheme", "PdfPosConv")

import math
import ctypes
import logging
import weakref
import pypdfium2.raw as pdfium_r
import pypdfium2.internal as pdfium_i
from pypdfium2._helpers.misc import PdfiumError
from pypdfium2._helpers.bitmap import PdfBitmap
from pypdfium2._helpers.textpage import PdfTextPage
from pypdfium2._helpers.pageobjects import PdfObject

c_float = ctypes.c_float
logger = logging.getLogger(__name__)


class PdfPage (pdfium_i.AutoCloseable):
    """
    Page helper class.
    
    Attributes:
        raw (FPDF_PAGE): The underlying PDFium page handle.
        pdf (PdfDocument): Reference to the document this page belongs to.
    """
    
    def __init__(self, raw, pdf, formenv):
        self.raw, self.pdf, self.formenv = raw, pdf, formenv
        super().__init__(PdfPage._close_impl, self.formenv)
    
    
    @staticmethod
    def _close_impl(raw, formenv):
        if formenv:
            pdfium_r.FORM_OnBeforeClosePage(raw, formenv)
        pdfium_r.FPDF_ClosePage(raw)
    
    
    @property
    def parent(self):  # AutoCloseable hook
        # Might want to have this point to the direct parent, i. e. (self.pdf if formenv is None else self.formenv), but this might confuse callers expecting that parent always be pdf for pages.
        return self.pdf
    
    
    def get_width(self):
        """
        Returns:
            float: Page width (horizontal size), in PDF canvas units.
        """
        return pdfium_r.FPDF_GetPageWidthF(self)
    
    def get_height(self):
        """
        Returns:
            float: Page height (vertical size), in PDF canvas units.
        """
        return pdfium_r.FPDF_GetPageHeightF(self)
    
    def get_size(self):
        """
        Returns:
            (float, float): Page width and height, in PDF canvas units.
        """
        return (self.get_width(), self.get_height())
    
    
    # NOTE {get,set}_rotation() deliberately fail with dict access error in case of invalid values
    
    def get_rotation(self):
        """
        Returns:
            int: Clockwise page rotation in degrees.
        """
        return pdfium_i.RotationToDegrees[ pdfium_r.FPDFPage_GetRotation(self) ]
    
    def set_rotation(self, rotation):
        """
        Define the absolute, clockwise page rotation (0, 90, 180, or 270 degrees).
        """
        pdfium_r.FPDFPage_SetRotation(self, pdfium_i.RotationToConst[rotation])
    
    
    def _get_box(self, box_func, fallback_func, fallback_ok):
        left, bottom, right, top = c_float(), c_float(), c_float(), c_float()
        ok = box_func(self, left, bottom, right, top)
        if not ok:
            return (fallback_func() if fallback_ok else None)
        return (left.value, bottom.value, right.value, top.value)
    
    # NOTE in case further arguments are needed (besides fallback_ok), then use *args, **kwargs in callers
    
    def get_mediabox(self, fallback_ok=True):
        """
        Returns:
            (float, float, float, float) | None:
            The page MediaBox in PDF canvas units, consisting of four coordinates (usually x0, y0, x1, y1).
            If MediaBox is not defined, returns ANSI A (0, 0, 612, 792) if ``fallback_ok=True``, None otherwise.
        Note:
            Due to quirks in PDFium's public API, all ``get_*box()`` functions except :meth:`.get_bbox`
            do not inherit from parent nodes in the page tree (as of PDFium 5418).
        """
        # https://crbug.com/pdfium/1786
        return self._get_box(pdfium_r.FPDFPage_GetMediaBox, lambda: (0, 0, 612, 792), fallback_ok)
    
    def set_mediabox(self, l, b, r, t):
        """
        Set the page's MediaBox by passing four :class:`float` coordinates (usually x0, y0, x1, y1).
        """
        pdfium_r.FPDFPage_SetMediaBox(self, l, b, r, t)
    
    def get_cropbox(self, fallback_ok=True):
        """
        Returns:
            The page's CropBox (If not defined, falls back to MediaBox).
        """
        return self._get_box(pdfium_r.FPDFPage_GetCropBox, self.get_mediabox, fallback_ok)
    
    def set_cropbox(self, l, b, r, t):
        """
        Set the page's CropBox.
        """
        pdfium_r.FPDFPage_SetCropBox(self, l, b, r, t)
    
    def get_bleedbox(self, fallback_ok=True):
        """
        Returns:
            The page's BleedBox (If not defined, falls back to CropBox).
        """
        return self._get_box(pdfium_r.FPDFPage_GetBleedBox, self.get_cropbox, fallback_ok)
    
    def set_bleedbox(self, l, b, r, t):
        """
        Set the page's BleedBox.
        """
        pdfium_r.FPDFPage_SetBleedBox(self, l, b, r, t)
    
    def get_trimbox(self, fallback_ok=True):
        """
        Returns:
            The page's TrimBox (If not defined, falls back to CropBox).
        """
        return self._get_box(pdfium_r.FPDFPage_GetTrimBox, self.get_cropbox, fallback_ok)
    
    def set_trimbox(self, l, b, r, t):
        """
        Set the page's TrimBox.
        """
        pdfium_r.FPDFPage_SetTrimBox(self, l, b, r, t)
    
    def get_artbox(self, fallback_ok=True):
        """
        Returns:
            The page's ArtBox (If not defined, falls back to CropBox).
        """
        return self._get_box(pdfium_r.FPDFPage_GetArtBox, self.get_cropbox, fallback_ok)
    
    def set_artbox(self, l, b, r, t):
        """
        Set the page's ArtBox.
        """
        pdfium_r.FPDFPage_SetArtBox(self, l, b, r, t)
    
    
    def get_bbox(self):
        """
        Returns:
            The bounding box of the page (the intersection between its media box and crop box).
        """
        rect = pdfium_r.FS_RECTF()
        ok = pdfium_r.FPDF_GetPageBoundingBox(self, rect)
        if not ok:
            raise PdfiumError("Failed to get page bounding box.")
        return (rect.left, rect.bottom, rect.right, rect.top)
    
    
    # TODO add bindings to FPDFPage_TransFormWithClip()
    
    
    def get_textpage(self):
        """
        Returns:
            PdfTextPage: A new text page handle for this page.
        """
        raw_textpage = pdfium_r.FPDFText_LoadPage(self)
        if not raw_textpage:
            raise PdfiumError("Failed to load text page.")
        textpage = PdfTextPage(raw_textpage, self)
        self._add_kid(textpage)
        return textpage
    
    
    def insert_obj(self, pageobj):
        """
        Insert a page object into the page.
        
        The page object must not belong to a page yet. If it belongs to a PDF, this page must be part of the PDF.
        
        Position and form are defined by the object's matrix.
        If it is the identity matrix, the object will appear as-is on the bottom left corner of the page.
        
        Parameters:
            pageobj (PdfObject): The page object to insert.
        """
        
        if pageobj.page:
            raise ValueError("The pageobject you attempted to insert already belongs to a page.")
        if pageobj.pdf and (pageobj.pdf is not self.pdf):
            raise ValueError("The pageobject you attempted to insert belongs to a different PDF.")
        
        pdfium_r.FPDFPage_InsertObject(self, pageobj)
        pageobj._detach_finalizer()
        pageobj.page = self
        pageobj.pdf = self.pdf
    
    
    def remove_obj(self, pageobj):
        """
        Remove a page object from the page.
        As of PDFium 5692, detached page objects may be only re-inserted into existing pages of the same document.
        If the page object is not re-inserted into a page, its ``close()`` method may be called.
        
        Parameters:
            pageobj (PdfObject): The page object to remove.
        """
        
        if pageobj.page is not self:
            raise ValueError("The page object you attempted to remove is not part of this page.")
        
        ok = pdfium_r.FPDFPage_RemoveObject(self, pageobj)
        if not ok:
            raise PdfiumError("Failed to remove pageobject.")
        
        pageobj.page = None
        pageobj._attach_finalizer()
    
    
    def gen_content(self):
        """
        Generate page content to apply additions, removals or modifications of page objects.
        
        If page content was changed, this function should be called once before saving the document or re-loading the page.
        """
        ok = pdfium_r.FPDFPage_GenerateContent(self)
        if not ok:
            raise PdfiumError("Failed to generate page content.")
    
    
    def get_objects(self, filter=None, max_depth=2, form=None, level=0):
        """
        Iterate through the page objects on this page.
        
        Parameters:
            filter (list[int] | None):
                An optional list of page object types to filter (:attr:`FPDF_PAGEOBJ_*`).
                Any objects whose type is not contained will be skipped.
                If None or empty, all objects will be provided, regardless of their type.
            max_depth (int):
                Maximum recursion depth to consider when descending into Form XObjects.
        
        Yields:
            :class:`.PdfObject`: A page object.
        """
        
        # CONSIDER close skipped objects explicitly ?
        
        if form:
            count_objects = pdfium_r.FPDFFormObj_CountObjects
            get_object = pdfium_r.FPDFFormObj_GetObject
            parent = form
        else:
            count_objects = pdfium_r.FPDFPage_CountObjects
            get_object = pdfium_r.FPDFPage_GetObject
            parent = self
        
        n_objects = count_objects(parent)
        if n_objects < 0:
            raise PdfiumError("Failed to get number of page objects.")
        
        for i in range(n_objects):
            
            raw_obj = get_object(parent, i)
            if raw_obj is None:
                raise PdfiumError("Failed to get page object.")
            
            helper_obj = PdfObject(raw_obj, page=self, pdf=self.pdf, level=level)
            self._add_kid(helper_obj)
            if not filter or helper_obj.type in filter:
                yield helper_obj
            
            if helper_obj.type == pdfium_r.FPDF_PAGEOBJ_FORM and level < max_depth-1:
                yield from self.get_objects(
                    filter = filter,
                    max_depth = max_depth,
                    form = raw_obj,
                    level = level + 1,
                )
    
    
    # non-public because it doesn't really work (returns success but does nothing on all samples we tried)
    def _flatten(self, flag=pdfium_r.FLAT_NORMALDISPLAY):
        """
        Attempt to flatten annotations and form fields into the page contents.
        
        Parameters:
            flag (int): PDFium flattening target (:attr:`FLAT_*`)
        Returns:
            int: PDFium flattening status (:attr:`FLATTEN_*`). :attr:`FLATTEN_FAIL` is handled internally.
        """
        rc = pdfium_r.FPDFPage_Flatten(self, flag)
        if rc == pdfium_r.FLATTEN_FAIL:
            raise PdfiumError("Failed to flatten annotations / form fields.")
        return rc
    
    
    # TODO
    # - add helpers for matrix-based and interruptible rendering
    # - add lower-level renderer that takes a caller-provided bitmap
    # e. g. render(), render_ex(), render_matrix(), render_matrix_ex()
    
    
    def render(
            self,
            scale = 1,
            rotation = 0,
            crop = (0, 0, 0, 0),
            may_draw_forms = True,
            bitmap_maker = PdfBitmap.new_native,
            color_scheme = None,
            fill_to_stroke = False,
            **kwargs
        ):
        """
        Rasterize the page to a :class:`.PdfBitmap`.
        
        Hint:
            If targetting a PIL image, consider rev_byteorder and prefer_bgrx for a pixel format natively supported by PIL (zero-copy).
        
        Parameters:
            
            scale (float):
                A factor scaling the number of pixels per PDF canvas unit. This defines the resolution of the image.
                To convert a DPI value to a scale factor, multiply it by the size of 1 canvas unit in inches (usually 1/72in). [#user_unit]_
            
            rotation (int):
                Additional rotation in degrees (0, 90, 180, or 270).
            
            crop (tuple[float, float, float, float]):
                Amount in PDF canvas units to cut off from page borders (left, bottom, right, top). Crop is applied after rotation.
            
            may_draw_forms (bool):
                If True, render form fields (provided the document has forms and :meth:`~PdfDocument.init_forms` was called).
            
            bitmap_maker (typing.Callable):
                Callback function used to create the :class:`.PdfBitmap`.
            
            fill_color (tuple[int, int, int, int]):
                Color the bitmap will be filled with before rendering (RGBA values from 0 to 255).
            
            grayscale (bool):
                If True, render in grayscale mode.
            
            optimize_mode (None | str):
                Page rendering optimization mode (None, "lcd", "print").
            
            draw_annots (bool):
                If True, render page annotations.
            
            no_smoothtext (bool):
                If True, disable text anti-aliasing. Overrides ``optimize_mode="lcd"``.
            
            no_smoothimage (bool):
                If True, disable image anti-aliasing.
            
            no_smoothpath (bool):
                If True, disable path anti-aliasing.
            
            force_halftone (bool):
                If True, always use halftone for image stretching.
            
            limit_image_cache (bool):
                If True, limit image cache size.
            
            rev_byteorder (bool):
                If True, render with reverse byte order, leading to ``RGB(A/X)`` output instead of ``BGR(A/X)``.
                Other pixel formats are not affected.
            
            prefer_bgrx (bool):
                If True, prefer four-channel over three-channel pixel formats, even if the alpha byte is unused.
                Other pixel formats are not affected.
            
            force_bitmap_format (int | None):
                If given, override automatic pixel format selection and enforce use of the given format (one of the :attr:`FPDFBitmap_*` constants).
            
            extra_flags (int):
                Additional PDFium rendering flags. May be combined with bitwise OR (``|`` operator).
            
            color_scheme (PdfColorScheme | None):
                Deprecated since v5. (An optional, custom rendering color scheme.)
            
            fill_to_stroke (bool):
                Deprecated since v5. (If True and rendering with custom color scheme, only draw borders around fill areas using the `path_stroke` color, instead of filling with the `path_fill` color.)
        
        Returns:
            PdfBitmap: Bitmap of the rendered page.
        
        .. deprecated:: 5
            *color_scheme* and *fill_to_stroke* considered not useful (see :class:`.PdfColorScheme`)
        
        .. [#user_unit] Since PDF 1.6, pages may define an additional user unit factor. In this case, 1 canvas unit is equivalent to ``user_unit * (1/72)`` inches. PDFium currently does not have an API to get the user unit, so this is not taken into account.
        """
        
        src_width  = math.ceil(self.get_width()  * scale)
        src_height = math.ceil(self.get_height() * scale)
        if rotation in (90, 270):
            src_width, src_height = src_height, src_width
        
        crop = [math.ceil(c*scale) for c in crop]
        width  = src_width  - crop[0] - crop[2]
        height = src_height - crop[1] - crop[3]
        if any(d < 1 for d in (width, height)):
            raise ValueError("Crop exceeds page dimensions")
        
        cl_format, rev_byteorder, fill_color, flags = _parse_renderopts(**kwargs)
        if color_scheme and fill_to_stroke:
            flags |= pdfium_r.FPDF_CONVERT_FILL_TO_STROKE
        
        bitmap = bitmap_maker(width, height, format=cl_format, rev_byteorder=rev_byteorder)
        bitmap.fill_rect(0, 0, width, height, fill_color)
        
        pos_args = (-crop[0], -crop[3], src_width, src_height, pdfium_i.RotationToConst[rotation])
        render_args = (bitmap, self, *pos_args, flags)
        
        if color_scheme is None:
            pdfium_r.FPDF_RenderPageBitmap(*render_args)
            
        else:
            pause = pdfium_r.IFSDK_PAUSE(version=1)
            pdfium_i.set_callback(pause, "NeedToPauseNow", lambda _: False)
            
            fpdf_cs = color_scheme.convert(rev_byteorder)
            status = pdfium_r.FPDF_RenderPageBitmapWithColorScheme_Start(*render_args, fpdf_cs, pause)
            assert status == pdfium_r.FPDF_RENDER_DONE
            pdfium_r.FPDF_RenderPage_Close(self)
        
        if may_draw_forms and self.formenv:
            pdfium_r.FPDF_FFLDraw(self.formenv, *render_args)
        
        bitmap._pos_args = (weakref.ref(self), *pos_args)
        return bitmap


def _auto_bitmap_format(fill_color, grayscale, prefer_bgrx):
    if fill_color[3] < 255:
        return pdfium_r.FPDFBitmap_BGRA
    elif grayscale:
        return pdfium_r.FPDFBitmap_Gray
    elif prefer_bgrx:
        return pdfium_r.FPDFBitmap_BGRx
    else:
        return pdfium_r.FPDFBitmap_BGR


def _parse_renderopts(
        fill_color = (255, 255, 255, 255),
        grayscale = False,
        optimize_mode = None,
        draw_annots = True,
        no_smoothtext = False,
        no_smoothimage = False,
        no_smoothpath = False,
        force_halftone = False,
        limit_image_cache = False,
        rev_byteorder = False,
        prefer_bgrx = False,
        force_bitmap_format = None,
        extra_flags = 0,
    ):
    
    if force_bitmap_format is None:
        cl_format = _auto_bitmap_format(fill_color, grayscale, prefer_bgrx)
    else:
        cl_format = force_bitmap_format
    
    if cl_format == pdfium_r.FPDFBitmap_Gray:
        rev_byteorder = False
    
    flags = extra_flags
    if grayscale:
        flags |= pdfium_r.FPDF_GRAYSCALE
    if draw_annots:
        flags |= pdfium_r.FPDF_ANNOT
    if no_smoothtext:
        flags |= pdfium_r.FPDF_RENDER_NO_SMOOTHTEXT
    if no_smoothimage:
        flags |= pdfium_r.FPDF_RENDER_NO_SMOOTHIMAGE
    if no_smoothpath:
        flags |= pdfium_r.FPDF_RENDER_NO_SMOOTHPATH
    if force_halftone:
        flags |= pdfium_r.FPDF_RENDER_FORCEHALFTONE
    if limit_image_cache:
        flags |= pdfium_r.FPDF_RENDER_LIMITEDIMAGECACHE
    if rev_byteorder:
        flags |= pdfium_r.FPDF_REVERSE_BYTE_ORDER
    
    if optimize_mode:
        optimize_mode = optimize_mode.lower()
        if optimize_mode == "lcd":
            flags |= pdfium_r.FPDF_LCD_TEXT
        elif optimize_mode == "print":
            flags |= pdfium_r.FPDF_PRINTING
        else:
            raise ValueError(f"Invalid optimize_mode {optimize_mode}")
    
    # CONSIDER using a namedtuple or something
    return cl_format, rev_byteorder, fill_color, flags


class PdfPosConv:
    """
    Pdf coordinate translator.
    
    Parameters:
        page (PdfPage):
            Handle to the page.
        bitmap (PdfBitmap):
            Handle to the bitmap, which must be a rendering of *page*.
    """
    
    # TODO add to test suite
    
    def __init__(self, page, bitmap):
        
        if not bitmap._pos_args:
            raise RuntimeError("This bitmap does not belong to a page.")
        
        assert page is not None
        orig_page = bitmap._pos_args[0]()
        if orig_page is not page:
            raise RuntimeError("This bitmap was not rendered from the given page.")
        
        self.page = page
        self._args = bitmap._pos_args[1:]
    
    
    def to_page(self, bitmap_x, bitmap_y):
        """
        Translate coordinates from bitmap to page.
        """
        page_x, page_y = ctypes.c_double(), ctypes.c_double()
        ok = pdfium_r.FPDF_DeviceToPage(self.page, *self._args, bitmap_x, bitmap_y, page_x, page_y)
        if not ok:
            raise PdfiumError("Failed to translate to page coordinates.")
        return (page_x.value, page_y.value)
    
    
    def to_bitmap(self, page_x, page_y):
        """
        Translate coordinates from page to bitmap.
        """
        bitmap_x, bitmap_y = ctypes.c_int(), ctypes.c_int()
        ok = pdfium_r.FPDF_PageToDevice(self.page, *self._args, page_x, page_y, bitmap_x, bitmap_y)
        if not ok:
            raise PdfiumError("Failed to translate to bitmap coordinates.")
        return (bitmap_x.value, bitmap_y.value)


class PdfColorScheme:
    """
    Forced rendering color scheme.
    Each color shall be provided as a list of values for red, green, blue and alpha, ranging from 0 to 255.
    Unspecified params will be transparent.
    
    .. deprecated:: 5
        This API has been considered not useful.
        PDFium forces the color params on all instances in question, regardless of their original color (flattening, information loss).
        This commonly leads to readability issues. For a dark theme, consider selective lightness inversion instead.
    """
    
    def __init__(self, path_fill=None, path_stroke=None, text_fill=None, text_stroke=None):
        self.colors = dict(
            path_fill_color=path_fill, path_stroke_color=path_stroke,
            text_fill_color=text_fill, text_stroke_color=text_stroke,
        )
    
    def convert(self, rev_byteorder):
        """
        Returns:
            The color scheme as :class:`FPDF_COLORSCHEME` object.
        """
        fpdf_cs = pdfium_r.FPDF_COLORSCHEME()
        for key, value in self.colors.items():
            if value is not None:
                setattr(fpdf_cs, key, pdfium_i.color_tohex(value, rev_byteorder))
        return fpdf_cs
