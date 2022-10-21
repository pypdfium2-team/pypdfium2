# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from ctypes import c_float
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.misc import (
    PdfiumError,
    get_fileaccess,
    is_input_buffer,
)
from pypdfium2._helpers.matrix import PdfMatrix


class PdfPageObject:
    """
    Page object helper class.
    
    When constructing a :class:`.PdfPageObject`, a more specific subclass may be returned instead,
    depending on :attr:`.type` (e. g. :class:`.PdfImageObject`).
    
    Note:
        Page objects are automatically freed by PDFium with the page they belong to.
        If a page object ends up without associated page, you may want to call ``FPDFPageObj_Destroy(pageobj.raw)``.
    
    Attributes:
        raw (FPDF_PAGEOBJECT):
            The underlying PDFium pageobject handle.
        type (int):
            The type of the object (:data:`FPDF_PAGEOBJ_*`), at the time of initialisation.
        page (PdfPage):
            Reference to the page this pageobject belongs to. May be :data:`None` if the object does not belong to a page yet.
        pdf (PdfDocument):
            Reference to the document this pageobject belongs to. May be :data:`None` if the object does not belong to a document yet.
            This attribute is always set if :attr:`.page` is set.
        level (int):
            Nesting level signifying the number of parent Form XObjects, at the time of initialisation.
            Zero if the object is not nested in a Form XObject.
    """
    
    
    def __new__(cls, raw, type, *args, **kwargs):
        # Allow to create a more specific helper depending on the type
        if type == pdfium.FPDF_PAGEOBJ_IMAGE:
            instance = super().__new__(PdfImageObject)
        else:
            instance = super().__new__(PdfPageObject)
        return instance
    
    
    def __init__(self, raw, type, page=None, pdf=None, level=0):
        
        self.raw = raw
        self.type = type
        self.page = page
        self.pdf = pdf
        self.level = level
        
        if page is not None:
            if self.pdf is None:
                self.pdf = page.pdf
            elif self.pdf is not page.pdf:
                raise ValueError("*page* must belong to *pdf* when constructing a pageobject.")
    
    
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


class PdfImageObject (PdfPageObject):
    """
    Image object helper class (specific kind of page object).
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @classmethod
    def new(cls, pdf):
        """
        Parameters:
            pdf (PdfDocument): The document to which the new image object shall be added.
        Returns:
            PdfImageObject: Handle to a new, empty image.
        """
        return cls(
            pdfium.FPDFPageObj_NewImageObj(pdf.raw),
            pdfium.FPDF_PAGEOBJ_IMAGE,
            page = None,
            pdf = pdf,
        )
    
    
    def load_jpeg(self, buffer, pages=None, inline=False, autoclose=True):
        """
        Load a JPEG into the image object.
        
        Position and size of the image are defined by its matrix.
        If the image is new, it will appear as a tiny square of 1x1 units on the bottom left corner of the page.
        Use :class:`.PdfMatrix` and :meth:`.set_matrix` to adjust the position.
        
        If replacing an image, the existing matrix will be preserved.
        If aspect ratios do not match, the new image will be squashed into the old image's boundaries.
        Modify the matrix manually if you wish to prevent this.
        
        Parameters:
            buffer (typing.BinaryIO):
                A readable byte buffer to access the JPEG data.
            pages (typing.Sequence[PdfPage] | None):
                If replacing an image, pass in a list of loaded pages that might contain the it, to update their cache.
                (The same image may be shown multiple times in different transforms across a PDF.)
                If the image object handle is new, this parameter may be :data:`None` or an empty list.
            inline (bool):
                Whether to load the image content into memory.
                If :data:`True`, the buffer may be closed after this function call.
                Otherwise, the buffer needs to remain open until the PDF is closed.
            autoclose (bool):
                Whether the buffer should be automatically closed once it is not needed anymore.
        
        Returns:
            (int, int): Image width and height in pixels.
        """
        
        if not is_input_buffer(buffer):
            raise ValueError("This is not a compatible buffer: %s" % buffer)
        
        fileaccess, ld_data = get_fileaccess(buffer)
        
        if inline:
            loader = pdfium.FPDFImageObj_LoadJpegFileInline
        else:
            loader = pdfium.FPDFImageObj_LoadJpegFile
        
        c_pages = None
        page_count = 0
        if pages:
            page_count = len(pages)
            c_pages = (pdfium.FPDF_PAGE * page_count)(*[p.raw for p in pages])
        
        success = loader(c_pages, page_count, self.raw, fileaccess)
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
        
        metadata = self.get_info()
        return (metadata.width, metadata.height)
    
    
    def get_info(self):
        """
        Returns:
            FPDF_IMAGEOBJ_METADATA:
            A structure containing information about the image object, including dimensions, DPI, bits per pixel, and colour space.
            If the image does not belong to a page yet, some values will be unset (0).
        """
        
        raw_page = (self.page.raw if self.page else None)
        
        metadata = pdfium.FPDF_IMAGEOBJ_METADATA()
        success = pdfium.FPDFImageObj_GetImageMetadata(self.raw, raw_page, metadata)
        if not success:
            raise PdfiumError("Failed to retrieve image metadata.")
        
        return metadata
