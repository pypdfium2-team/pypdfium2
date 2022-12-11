# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ["PdfObject", "PdfImage"]

import ctypes
from pathlib import Path
from collections import namedtuple
import pypdfium2.raw as pdfium_c
from pypdfium2._helpers.misc import PdfiumError
from pypdfium2._helpers.matrix import PdfMatrix
from pypdfium2._helpers.bitmap import PdfBitmap
from pypdfium2._helpers._internal import consts, utils
from pypdfium2._helpers._internal.autoclose import AutoCloseable

try:
    import PIL.Image
except ImportError:
    PIL = None

c_float = ctypes.c_float


class PdfObject (AutoCloseable):
    """
    Page object helper class.
    
    When constructing a :class:`.PdfObject`, an instance of a more specific subclass may be returned instead,
    depending on the object's :attr:`.type` (e. g. :class:`.PdfImage`).
    
    Attributes:
        raw (FPDF_PAGEOBJECT):
            The underlying PDFium pageobject handle.
        type (int):
            The object's type (:data:`FPDF_PAGEOBJ_*`).
        page (PdfPage):
            Reference to the page this pageobject belongs to. May be None if it does not belong to a page yet.
        pdf (PdfDocument):
            Reference to the document this pageobject belongs to. May be None if the object does not belong to a document yet.
            This attribute is always set if :attr:`.page` is set.
        level (int):
            Nesting level signifying the number of parent Form XObjects, at the time of construction.
            Zero if the object is not nested in a Form XObject.
    """
    
    
    def __new__(cls, raw, *args, **kwargs):
        
        type = pdfium_c.FPDFPageObj_GetType(raw)
        if type == pdfium_c.FPDF_PAGEOBJ_IMAGE:
            instance = super().__new__(PdfImage)
        else:
            instance = super().__new__(PdfObject)
        
        instance.type = type
        return instance
    
    
    def __init__(self, raw, page=None, pdf=None, level=0):
        
        self.raw = raw
        self.page = page
        self.pdf = pdf
        self.level = level
        
        if page is not None:
            if self.pdf is None:
                self.pdf = page.pdf
            elif self.pdf is not page.pdf:
                raise ValueError("*page* must belong to *pdf* when constructing a pageobject.")
        
        AutoCloseable.__init__(self, pdfium_c.FPDFPageObj_Destroy, needs_free=(page is None))
    
    
    @property
    def parent(self):
        if self.page is not None:
            return self.page
        else:
            return self.pdf  # may be none
    
    
    def get_pos(self):
        """
        Get the position of the object on the page.
        
        Returns:
            A tuple of four :class:`float` coordinates for left, bottom, right, and top.
        """
        if self.page is None:
            raise RuntimeError("Must not call get_pos() on a loose pageobject.")
        
        left, bottom, right, top = c_float(), c_float(), c_float(), c_float()
        success = pdfium_c.FPDFPageObj_GetBounds(self.raw, left, bottom, right, top)
        if not success:
            raise PdfiumError("Failed to locate pageobject.")
        
        return (left.value, bottom.value, right.value, top.value)
    
    
    def get_matrix(self):
        """
        Returns:
            PdfMatrix: The pageobject's current transform matrix.
        """
        fs_matrix = pdfium_c.FS_MATRIX()
        success = pdfium_c.FPDFPageObj_GetMatrix(self.raw, fs_matrix)
        if not success:
            raise PdfiumError("Failed to get matrix of pageobject.")
        return PdfMatrix.from_pdfium(fs_matrix)
    
    
    def set_matrix(self, matrix):
        """
        Parameters:
            matrix (PdfMatrix): Set this matrix as the pageobject's transform matrix.
        """
        if not isinstance(matrix, PdfMatrix):
            raise ValueError("*matrix* must be a PdfMatrix object.")
        success = pdfium_c.FPDFPageObj_SetMatrix(self.raw, matrix.to_pdfium())
        if not success:
            raise PdfiumError("Failed to set matrix of pageobject.")
    
    
    def transform(self, matrix):
        """
        Parameters:
            matrix (PdfMatrix): Multiply the page object's current transform matrix by this matrix.
        """
        if not isinstance(matrix, PdfMatrix):
            raise ValueError("*matrix* must be a PdfMatrix object.")
        pdfium_c.FPDFPageObj_Transform(self.raw, *matrix.get())


# In principle, we would like to move PdfImage to a separate file, but it's not that easy because of the two-fold connection with PdfObject, which would run us into a circular import. (However, what we could do is externalize the class under a different name and turn PdfImage into a wrapper which merely inherits from that class.)

class PdfImage (PdfObject):
    """
    Image object helper class (specific kind of page object).
    """
    
    #: Filters applied by :func:`FPDFImageObj_GetImageDataDecoded`. Hereafter referred to as "simple filters", while non-simple filters will be called "complex filters".
    SIMPLE_FILTERS = ("ASCIIHexDecode", "ASCII85Decode", "RunLengthDecode", "FlateDecode", "LZWDecode")
    
    
    @classmethod
    def new(cls, pdf):
        """
        Parameters:
            pdf (PdfDocument): The document to which the new image object shall be added.
        Returns:
            PdfImage: Handle to a new, empty image.
            Note that position and size of the image are defined by its matrix, which defaults to the identity matrix.
            This means that new images will appear as a tiny square of 1x1 units on the bottom left corner of the page.
            Use :class:`.PdfMatrix` and :meth:`.set_matrix` to adjust size and position.
        """
        return cls(
            pdfium_c.FPDFPageObj_NewImageObj(pdf.raw),
            page = None,
            pdf = pdf,
        )
    
    
    def get_metadata(self):
        """
        Retrieve image metadata, including dimensions, DPI, bits per pixel, and color space.
        If the image does not belong to a page yet, bits per pixel and color space will be unset (0).
        
        Note:
            * The DPI values signify the resolution of the image on the PDF page, not the DPI metadata embedded in the image file.
            * Due to issues in PDFium, this function can be inefficient.
        
        Returns:
            FPDF_IMAGEOBJ_METADATA: Image metadata structure
        """
        
        # https://crbug.com/pdfium/1928
        
        raw_page = (self.page.raw if self.page else None)
        metadata = pdfium_c.FPDF_IMAGEOBJ_METADATA()
        success = pdfium_c.FPDFImageObj_GetImageMetadata(self.raw, raw_page, metadata)
        if not success:
            raise PdfiumError("Failed to get image metadata.")
        
        return metadata
    
    
    def load_jpeg(self, source, pages=None, inline=False, autoclose=True):
        """
        Set a JPEG as the image object's content.
        
        Parameters:
            source (str | pathlib.Path | typing.BinaryIO):
                Input JPEG, given as file path or readable byte buffer.
            pages (list[PdfPage] | None):
                If replacing an image, pass in a list of loaded pages that might contain it, to update their cache.
                (The same image may be shown multiple times in different transforms across a PDF.)
                May be None or an empty sequence if the image is not shared.
            inline (bool):
                Whether to load the image content into memory. If True, the buffer may be closed after this function call.
                Otherwise, the buffer needs to remain open until the PDF is closed.
            autoclose (bool):
                If the input is a buffer, whether it should be automatically closed once not needed by the PDF anymore.
        """
        
        if isinstance(source, (str, Path)):
            buffer = open(source, "rb")
            autoclose = True
        elif utils.is_buffer(source, "r"):
            buffer = source
        else:
            raise ValueError("Cannot load JPEG from %s - not a file path or byte buffer." % (source, ))
        
        bufaccess, ld_data = utils.get_bufreader(buffer)
        
        if inline:
            loader = pdfium_c.FPDFImageObj_LoadJpegFileInline
        else:
            loader = pdfium_c.FPDFImageObj_LoadJpegFile
        
        c_pages, page_count = utils.pages_c_array(pages)
        success = loader(c_pages, page_count, self.raw, bufaccess)
        if not success:
            raise PdfiumError("Failed to load JPEG into image object.")
        
        if inline:
            for data in ld_data:
                id(data)
            if autoclose:
                buffer.close()
        else:
            self.pdf._data_holder += ld_data
            if autoclose:
                self.pdf._data_closer.append(buffer)
    
    
    def set_bitmap(self, bitmap, pages=None):
        """
        Set a bitmap as the image object's content.
        The pixel data will be flate compressed (as of PDFium 5418).
        
        Parameters:
            bitmap (PdfBitmap):
                The bitmap to inject into the image object.
            pages (list[PdfPage] | None):
                A list of loaded pages that might contain the image object. See :meth:`.load_jpeg`.
        """
        c_pages, page_count = utils.pages_c_array(pages)
        success = pdfium_c.FPDFImageObj_SetBitmap(c_pages, page_count, self.raw, bitmap.raw)
        if not success:
            raise PdfiumError("Failed to set image to bitmap.")
    
    
    def get_bitmap(self, render=False):
        """
        Get a bitmap rasterization of the image.
        
        Parameters:
            render (bool):
                Whether the image should be rendered, thereby applying possible transform matrices and alpha masks.
        Returns:
            PdfBitmap: Image bitmap (with a buffer allocated by PDFium).
        """
        
        if render:
            if self.pdf is None:
                raise RuntimeError("Cannot get rendered bitmap of loose page object.")
            raw_page = (self.page.raw if self.page else None)
            raw_bitmap = pdfium_c.FPDFImageObj_GetRenderedBitmap(self.pdf.raw, raw_page, self.raw)
        else:
            raw_bitmap = pdfium_c.FPDFImageObj_GetBitmap(self.raw)
        
        if raw_bitmap is None:
            raise PdfiumError("Failed to get bitmap of image %s." % self)
        
        return PdfBitmap.from_raw(raw_bitmap)
    
    
    def get_data(self, decode_simple=False):
        """
        Parameters:
            decode_simple (bool):
                If True, apply simple filters, resulting in semi-decoded data (see :attr:`.SIMPLE_FILTERS`).
                Otherwise, the raw data will be returned.
        Returns:
            ctypes.Array: The data of the image stream (as :class:`ctypes.c_ubyte` array).
        """
        
        if decode_simple:
            # apply simple filters (see https://crbug.com/pdfium/1203 for description)
            func = pdfium_c.FPDFImageObj_GetImageDataDecoded
        else:
            func = pdfium_c.FPDFImageObj_GetImageDataRaw
        
        n_bytes = func(self.raw, None, 0)
        buffer = (ctypes.c_ubyte * n_bytes)()
        func(self.raw, buffer, n_bytes)
        
        return buffer
    
    
    def get_filters(self, skip_simple=False):
        """
        Parameters:
            skip_simple (bool):
                If True, exclude simple filters.
        Returns:
            list[str]: A list of image filters, to be applied in order (from lowest to highest index).
        """
        
        filters = []
        count = pdfium_c.FPDFImageObj_GetImageFilterCount(self.raw)
        
        for i in range(count):
            length = pdfium_c.FPDFImageObj_GetImageFilter(self.raw, i, None, 0)
            buffer = ctypes.create_string_buffer(length)
            pdfium_c.FPDFImageObj_GetImageFilter(self.raw, i, buffer, length)
            f = buffer.value.decode("utf-8")
            if skip_simple and f in self.SIMPLE_FILTERS:
                continue
            filters.append(f)
        
        return filters
    
    
    def extract(self, dest, *args, **kwargs):
        """
        Extract the image into an independently usable file or byte buffer.
        Where possible, it will be attempted to transfer the image data directly, avoiding an unnecessary layer of decoding and re-encoding.
        Otherwise, the fully decoded data will be retrieved and (re-)encoded using :mod:`PIL`.
        
        Note that this function is quite limited because PDFium's public API does not expose all required information.
        Only DCTDecode (JPEG) and JPXDecode (JPEG 2000) images can be extracted directly.
        For images with complex filters, the bitmap data is used. Otherwise, ``get_data(decode_simple=True)`` is used.
        
        Parameters:
            dest (str | io.BytesIO):
                File path or byte buffer to which the image shall be written.
            fb_format (str):
                The image format to use in case it is necessary to (re-)encode the data.
            fb_render (bool):
                Whether the image should be rendered if falling back to bitmap-based extraction.
        """
        
        # https://crbug.com/pdfium/1930
        
        extraction_gen = _extract_smart(self, *args, **kwargs)
        format = next(extraction_gen)
        
        if isinstance(dest, (str, Path)):
            with open("%s.%s" % (dest, format), "wb") as buf:
                extraction_gen.send(buf)
        elif utils.is_buffer(dest, "w"):
            extraction_gen.send(dest)
        else:
            raise ValueError("Cannot extract to '%s'" % (dest, ))


ImageInfo = namedtuple("ImageInfo", "format mode metadata all_filters complex_filters")


class ImageNotExtractableError (Exception):
    pass


def _get_pil_mode(colorspace, bpp):
    # In theory, indexed (palettized) and ICC-based color spaces could be handled as well, but PDFium currently does not provide access to the palette or the ICC profile
    if colorspace == pdfium_c.FPDF_COLORSPACE_DEVICEGRAY:
        if bpp == 1:
            return "1"
        else:
            return "L"
    elif colorspace == pdfium_c.FPDF_COLORSPACE_DEVICERGB:
        return "RGB"
    elif colorspace == pdfium_c.FPDF_COLORSPACE_DEVICECMYK:
        return "CMYK"
    else:
        return None


def _extract_smart(image_obj, fb_format=None, fb_render=False):
    
    pil_image = None
    data = None
    info = None
    
    try:
        data, info = _extract_direct(image_obj)
    except ImageNotExtractableError:
        pil_image = image_obj.get_bitmap(render=fb_render).to_pil()
    else:
        format = info.format
        if format == "raw":
            metadata = info.metadata
            pil_image = PIL.Image.frombuffer(
                info.mode,
                (metadata.width, metadata.height),
                image_obj.get_data(decode_simple=True),
                "raw", info.mode, 0, 1,
            )
    
    if pil_image:
        if fb_format:
            format = fb_format
        elif pil_image.mode == "CMYK":
            format = "tiff"
        else:
            format = "png"
    
    # provide format, receive buffer
    buffer = yield format
    
    if pil_image:
        pil_image.save(buffer, format=format)
    else:
        buffer.write(data)
    
    # breakpoint preventing StopIteration on send()
    yield None


def _extract_direct(image_obj):
    
    all_filters = image_obj.get_filters()
    complex_filters = [f for f in all_filters if f not in PdfImage.SIMPLE_FILTERS]
    metadata = image_obj.get_metadata()
    mode = _get_pil_mode(metadata.colorspace, metadata.bits_per_pixel)
    
    out_data = None
    out_format = None
    
    # Not sure if FlateDecode or LZWDecode data could be wrapped directly in an image file structure like PNG or TIFF
    
    if len(complex_filters) == 0:
        if mode:
            out_data = image_obj.get_data(decode_simple=True)
            out_format = "raw"
        else:
            raise ImageNotExtractableError(
                "Unhandled color space %s - don't know how to treat data" % (consts.ColorspaceToStr[metadata.colorspace], )
            )
    
    elif len(complex_filters) == 1:
        f = complex_filters[0]
        if f == "DCTDecode":
            out_data = image_obj.get_data(decode_simple=True)
            out_format = "jpg"
        elif f == "JPXDecode":
            out_data = image_obj.get_data(decode_simple=True)
            out_format = "jp2"
        else:
            raise ImageNotExtractableError("Unhandled complex filter %s" % f)
        
        # Other complex filters:
        # CCITTFaxDecode: In theory, could be extracted directly (with a TIFF header builder like pikepdf/models/_transcoding.py:generate_ccitt_header), but PDFium doesn't tell us which CCITT group encoding it is.
        # JBIG2Decode: In PDF, JBIG2 header info is stripped, and global segments may be stored in a separate stream. In that form, the data would probably not be of much use, except perhaps for direct re-insertion into another PDF. We're not sure if it would be possible to re-combine this into a single JBIG2 file, or if any application could use this at all. PDFium doesn't provide us with the global segments, anyway.
    
    else:
        raise ImageNotExtractableError("Cannot handle multiple complex filters %s" % (complex_filters, ))
    
    info = ImageInfo(out_format, mode, metadata, all_filters, complex_filters)
    return out_data, info
