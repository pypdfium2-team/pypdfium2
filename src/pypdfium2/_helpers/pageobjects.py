# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause
# TODO rename file to pageobjects.py or objects.py

import ctypes
import weakref
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.misc import (
    PdfiumError,
    get_bufaccess,
    is_input_buffer,
)
from pypdfium2._helpers.matrix import PdfMatrix
from pypdfium2._helpers.bitmap import PdfBitmap

c_float = ctypes.c_float


class PdfObject:
    """
    Page object helper class.
    
    When constructing a :class:`.PdfObject`, an instance of a more specific subclass may be returned instead,
    depending on the object's :attr:`.type` (e. g. :class:`.PdfImage`).
    
    Attributes:
        raw (FPDF_PAGEOBJECT):
            The underlying PDFium pageobject handle.
        type (int):
            The type of the object (:data:`FPDF_PAGEOBJ_*`), at the time of construction.
        page (PdfPage):
            Reference to the page this pageobject belongs to. May be :data:`None` if the object does not belong to a page yet.
        pdf (PdfDocument):
            Reference to the document this pageobject belongs to. May be :data:`None` if the object does not belong to a document yet.
            This attribute is always set if :attr:`.page` is set.
        level (int):
            Nesting level signifying the number of parent Form XObjects, at the time of construction.
            Zero if the object is not nested in a Form XObject.
    """
    
    
    def __new__(cls, raw, *args, **kwargs):
        
        type = pdfium.FPDFPageObj_GetType(raw)
        if type == pdfium.FPDF_PAGEOBJ_IMAGE:
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
        
        self._finalizer = None
        if not self.page:
            self._attach_finalizer()
    
    
    # TODO smart finalizer testing
    
    @staticmethod
    def _static_close(raw):
        # only called on loose page objects
        pdfium.FPDFPageObj_Destroy(raw)
    
    def _attach_finalizer(self):
        assert self._finalizer is None
        self._finalizer = weakref.finalize(self, self._static_close, self.raw)
    
    def _detach_finalizer(self):
        self._finalizer.detach()
        self._finalizer = None
    
    
    def get_pos(self):
        """
        Get the position of the object on the page.
        
        Returns:
            A tuple of four :class:`float` coordinates for left, bottom, right, and top.
        """
        if self.page is None:
            raise RuntimeError("Must not call get_pos() on a loose pageobject.")
        
        left, bottom, right, top = c_float(), c_float(), c_float(), c_float()
        success = pdfium.FPDFPageObj_GetBounds(self.raw, left, bottom, right, top)
        if not success:
            raise PdfiumError("Failed to locate pageobject.")
        
        return (left.value, bottom.value, right.value, top.value)
    
    
    def get_matrix(self):
        """
        Returns:
            PdfMatrix: The pageobject's current transform matrix.
        """
        fs_matrix = pdfium.FS_MATRIX()
        success = pdfium.FPDFPageObj_GetMatrix(self.raw, fs_matrix)
        if not success:
            raise PdfiumError("Failed to get matrix of pageobject.")
        return PdfMatrix.from_pdfium(fs_matrix)
    
    
    def set_matrix(self, matrix):
        """
        Define *matrix* as the pageobject's transform matrix.
        """
        if not isinstance(matrix, PdfMatrix):
            raise ValueError("*matrix* must be a PdfMatrix object.")
        success = pdfium.FPDFPageObj_SetMatrix(self.raw, matrix.to_pdfium())
        if not success:
            raise PdfiumError("Failed to set matrix of pageobject.")
    
    
    def transform(self, matrix):
        """
        Apply *matrix* on top of the pageobject's current transform matrix.
        """
        if not isinstance(matrix, PdfMatrix):
            raise ValueError("*matrix* must be a PdfMatrix object.")
        pdfium.FPDFPageObj_Transform(self.raw, *matrix.get())


class PdfImage (PdfObject):
    """
    Image object helper class (specific kind of page object).
    """
    
    # uses constructor/initialiser of parent class
    
    @classmethod
    def new(cls, pdf):
        """
        Parameters:
            pdf (PdfDocument): The document to which the new image object shall be added.
        Returns:
            PdfImage: Handle to a new, empty image.
        """
        return cls(
            pdfium.FPDFPageObj_NewImageObj(pdf.raw),
            page = None,
            pdf = pdf,
        )
    
    
    def load_jpeg(self, buffer, pages=None, inline=False, autoclose=True):
        """
        Load a JPEG into the image object.
        
        Position and size of the image are defined by its matrix.
        If the image is new, it will appear as a tiny square of 1x1 units on the bottom left corner of the page.
        Use :class:`.PdfMatrix` and :meth:`.set_matrix` to adjust size and position.
        
        If replacing an image, the existing matrix will be preserved.
        If aspect ratios do not match, this means the new image will be squashed into the old image's boundaries.
        The matrix may be modified manually to prevent this.
        
        Parameters:
            buffer (typing.BinaryIO):
                A readable byte buffer to access the JPEG data.
            pages (typing.Sequence[PdfPage] | None):
                If replacing an image, pass in a list of loaded pages that might contain it, to update their cache.
                (The same image may be shown multiple times in different transforms across a PDF.)
                May be :data:`None` or an empty sequence if the image is not shared.
            inline (bool):
                Whether to load the image content into memory.
                If :data:`True`, the buffer may be closed after this function call.
                Otherwise, the buffer needs to remain open until the PDF is closed.
            autoclose (bool):
                Whether the buffer should be automatically closed once it is not needed anymore.
        """
        
        if not is_input_buffer(buffer):
            raise ValueError("This is not a compatible buffer: %s" % buffer)
        
        bufaccess, ld_data = get_bufaccess(buffer)
        
        if inline:
            loader = pdfium.FPDFImageObj_LoadJpegFileInline
        else:
            loader = pdfium.FPDFImageObj_LoadJpegFile
        
        c_pages = None
        page_count = 0
        if pages:
            page_count = len(pages)
            c_pages = (pdfium.FPDF_PAGE * page_count)(*[p.raw for p in pages])
        
        success = loader(c_pages, page_count, self.raw, bufaccess)
        if not success:
            raise PdfiumError("Loading JPEG into image object failed.")
        
        if inline:
            id(ld_data)
            if autoclose:
                buffer.close()
        else:
            self.pdf._data_holder += ld_data
            if autoclose:
                self.pdf._data_closer.append(buffer)
    
    
    def get_metadata(self):
        """
        Retrieve image metadata, including dimensions, DPI, bits per pixel, and colour space.
        If the image does not belong to a page yet, bits per pixel and colour space will be unset (0).
        
        Note that the DPI values signify the resolution of the image on the PDF page, not the DPI metadata embedded in the image file.
        
        Returns:
            FPDF_IMAGEOBJ_METADATA: Image metadata structure
        """
        
        raw_page = (self.page.raw if self.page else None)
        metadata = pdfium.FPDF_IMAGEOBJ_METADATA()
        success = pdfium.FPDFImageObj_GetImageMetadata(self.raw, raw_page, metadata)
        if not success:
            raise PdfiumError("Failed to retrieve image metadata.")
        
        return metadata
    
    
    def get_size(self):
        """
        TODO
        """
        metadata = self.get_metadata()
        return (metadata.width, metadata.height)
    
    
    def get_bitmap(self, render=False):
        """
        Get a bitmap rasterization of the image.
        
        Parameters:
            render (bool):
                Whether a possible alpha mask and transform matrix should be applied.
        Returns:
            PdfBitmap: Bitmap of the image (the buffer is allocated by PDFium internally).
        """
        
        if render:
            if self.pdf is None:
                raise RuntimeError("Cannot get rendered bitmap of loose page object.")
            raw_page = (self.page.raw if self.page else None)
            raw_bitmap = pdfium.FPDFImageObj_GetRenderedBitmap(self.pdf.raw, raw_page, self.raw)
        else:
            raw_bitmap = pdfium.FPDFImageObj_GetBitmap(self.raw)
        
        if raw_bitmap is None:
            raise PdfiumError("Failed to get bitmap of image object %s" % self)
        
        return PdfBitmap.from_raw(raw_bitmap)
