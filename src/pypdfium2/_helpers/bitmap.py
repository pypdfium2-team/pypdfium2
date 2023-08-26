# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PdfBitmap", )

import ctypes
import logging
import pypdfium2.raw as pdfium_r
import pypdfium2.internal as pdfium_i
from pypdfium2._helpers.misc import PdfiumError

logger = logging.getLogger(__name__)

try:
    import PIL.Image
except ImportError:
    PIL = None

try:
    import numpy
except ImportError:
    numpy = None


class PdfBitmap (pdfium_i.AutoCloseable):
    """
    Bitmap helper class.
    
    Warning:
        ``bitmap.close()``, which frees the buffer of foreign bitmaps, is not validated for safety.
        A bitmap must not be closed while other objects still depend on its buffer!
    
    .. _PIL Modes: https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes
    
    Attributes:
        raw (FPDF_BITMAP):
            The underlying PDFium bitmap handle.
        buffer (~ctypes.c_ubyte | bytes):
            A buffer containing the pixel data. May be either mutable or immutable, depening on how the bitmap was created.
        width (int):
            Width of the bitmap (horizontal size).
        height (int):
            Height of the bitmap (vertical size).
        stride (int):
            Number of bytes per line in the bitmap buffer.
            Depending on how the bitmap was created, there may be a padding of unused bytes at the end of each line, so this value can be greater than ``width * n_channels``.
        format (int):
            PDFium bitmap format constant (:attr:`FPDFBitmap_*`)
        rev_byteorder (bool):
            Whether the bitmap is using reverse byte order.
        n_channels (int):
            Number of channels per pixel.
        mode (str):
            The bitmap format as string (see `PIL Modes`_).
    
    Hint:
        If descriptive attributes are needed beyond the scope of the original bitmap buffer,
        be sure to detach them from them bitmap, to avoid holding the buffer in memory unnecessarily.
    """
    
    def __init__(self, raw, buffer, width, height, stride, format, rev_byteorder, needs_free):
        
        self.raw = raw
        self.buffer = buffer
        self.width, self.height = width, height
        self.stride = stride
        self.format = format
        self.rev_byteorder = rev_byteorder
        self.n_channels = pdfium_i.BitmapTypeToNChannels[self.format]
        self.mode = (pdfium_i.BitmapTypeToStrReverse if self.rev_byteorder else pdfium_i.BitmapTypeToStr)[self.format]
        
        # slot to store arguments for PdfPosConv, set on page rendering
        self._pos_args = None
        
        if needs_free:
            super().__init__(pdfium_r.FPDFBitmap_Destroy, obj=self.buffer)
    
    
    @property
    def parent(self):  # AutoCloseable hook
        return None
    
    
    @classmethod
    def from_raw(cls, raw, rev_byteorder=False, ex_buffer=None):
        """
        Construct a :class:`.PdfBitmap` wrapper around a raw PDFium bitmap handle.
        
        Parameters:
            raw (FPDF_BITMAP):
                PDFium bitmap handle.
            rev_byteorder (bool):
                Whether the bitmap uses reverse byte order.
            ex_buffer (~ctypes.c_ubyte | None):
                If the bitmap was created from a buffer allocated by Python/ctypes, pass in the ctypes array to keep it referenced.
        """
        
        width = pdfium_r.FPDFBitmap_GetWidth(raw)
        height = pdfium_r.FPDFBitmap_GetHeight(raw)
        format = pdfium_r.FPDFBitmap_GetFormat(raw)
        stride = pdfium_r.FPDFBitmap_GetStride(raw)
        
        if ex_buffer is None:
            needs_free = True
            first_item = pdfium_r.FPDFBitmap_GetBuffer(raw)
            if first_item.value is None:
                raise PdfiumError("Failed to get bitmap buffer (null pointer returned)")
            buffer = ctypes.cast(first_item, ctypes.POINTER(ctypes.c_ubyte * (stride * height))).contents
        else:
            needs_free = False
            buffer = ex_buffer
        
        return cls(
            raw=raw, buffer=buffer, width=width, height=height, stride=stride,
            format=format, rev_byteorder=rev_byteorder, needs_free=needs_free,
        )
    
    
    # TODO support setting stride if external buffer is provided
    @classmethod
    def new_native(cls, width, height, format, rev_byteorder=False, buffer=None):
        """
        Create a new bitmap using :func:`FPDFBitmap_CreateEx`, with a buffer allocated by Python/ctypes.
        Bitmaps created by this function are packed (no unused bytes between lines).
        """
        
        stride = width * pdfium_i.BitmapTypeToNChannels[format]
        if buffer is None:
            buffer = (ctypes.c_ubyte * (stride * height))()
        raw = pdfium_r.FPDFBitmap_CreateEx(width, height, format, buffer, stride)
        
        # alternatively, we could call the constructor directly with the information from above
        return cls.from_raw(raw, rev_byteorder, buffer)
    
    
    @classmethod
    def new_foreign_simple(cls, width, height, use_alpha, rev_byteorder=False):
        """
        Create a new bitmap using :func:`FPDFBitmap_Create`. The buffer is allocated by pdfium.
        
        The resulting buffer is supposed to be packed (no unused bytes between lines),
        and the first byte double word aligned. If the OS allows, the pdfium function can allocate up to 4 GB of memory.
        
        See :meth:`.new_foreign` for an alternative function that supports more pixel formats.
        """
        raw = pdfium_r.FPDFBitmap_Create(width, height, use_alpha)
        return cls.from_raw(raw, rev_byteorder)
    
    
    @classmethod
    def new_foreign(cls, width, height, format, rev_byteorder=False, force_packed=False):
        """
        Create a new bitmap using :func:`FPDFBitmap_CreateEx`, with a buffer allocated by pdfium.
        
        An alternative function is :meth:`.new_foreign_simple`, but it suppotrs less pixel formats.
        
        Parameters:
            force_packed (bool):
                If False (the default), there may be a gap of unused bytes between lines (offset = :attr:`.stride` - width*n_channels).
                Otherwise, attempt to force pdfium to create a packed buffer.
        """
        stride = width * pdfium_i.BitmapTypeToNChannels[format] if force_packed else 0
        raw = pdfium_r.FPDFBitmap_CreateEx(width, height, format, None, stride)
        return cls.from_raw(raw, rev_byteorder)
    
    
    def fill_rect(self, left, top, width, height, color):
        """
        Fill a rectangle on the bitmap with the given color.
        The coordinate system starts at the top left corner of the image.
        
        Note:
            This function replaces the color values in the given rectangle. It does not perform alpha compositing.
        
        Parameters:
            color (tuple[int, int, int, int]):
                RGBA fill color (a tuple of 4 integers ranging from 0 to 255).
        """
        c_color = pdfium_i.color_tohex(color, self.rev_byteorder)
        pdfium_r.FPDFBitmap_FillRect(self, left, top, width, height, c_color)
    
    
    # Requirement: If the result is a view of the buffer (not a copy), it keeps the referenced memory valid.
    # 
    # Note that memory management differs between native and foreign bitmap buffers:
    # - With native bitmaps, the memory is allocated by python on creation of the buffer object (transparent).
    # - With foreign bitmaps, the buffer object is merely a view of memory allocated by pdfium and will be freed by finalizer (opaque).
    # 
    # It is necessary that receivers correctly handle both cases, e.g. by keeping the buffer object itself alive.
    # As of May 2023, this seems to hold true for NumPy and PIL. New converters should be carefully tested.
    # 
    # We could consider attaching a buffer keep-alive finalizer to any converted objects referencing the buffer,
    # but then we'd have to rely on third parties to actually create a reference at all times, otherwise we would unnecessarily delay releasing memory.
    
    
    def to_numpy(self):
        """
        Convert the bitmap to a :mod:`numpy` array.
        
        The array contains as many rows as the bitmap is high.
        Each row contains as many pixels as the bitmap is wide.
        The length of each pixel corresponds to the number of channels.
        
        The resulting array is supposed to share memory with the original bitmap buffer,
        so changes to the buffer should be reflected in the array, and vice versa.
        
        Returns:
            numpy.ndarray: NumPy array (representation of the bitmap buffer).
        """
        
        # https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html#numpy.ndarray
        
        array = numpy.ndarray(
            # layout: row major
            shape = (self.height, self.width, self.n_channels),
            dtype = ctypes.c_ubyte,
            buffer = self.buffer,
            # number of bytes per item for each nesting level (outer->inner, i. e. row, pixel, value)
            strides = (self.stride, self.n_channels, 1),
        )
        
        return array
    
    
    def to_pil(self):
        """
        Convert the bitmap to a :mod:`PIL` image, using :func:`PIL.Image.frombuffer`.
        
        For ``RGBA``, ``RGBX`` and ``L`` buffers, PIL is supposed to share memory with
        the original bitmap buffer, so changes to the buffer should be reflected in the image, and vice versa.
        Otherwise, PIL will make a copy of the data.
        
        Returns:
            PIL.Image.Image: PIL image (representation or copy of the bitmap buffer).
        """
        
        # https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.frombuffer
        # https://pillow.readthedocs.io/en/stable/handbook/writing-your-own-image-plugin.html#the-raw-decoder
        
        dest_mode = pdfium_i.BitmapTypeToStrReverse[self.format]
        image = PIL.Image.frombuffer(
            dest_mode,                  # target color format
            (self.width, self.height),  # size
            self.buffer,                # buffer
            "raw",                      # decoder
            self.mode,                  # input color format
            self.stride,                # bytes per line
            1,                          # orientation (top->bottom)
        )
        image.readonly = False
        
        return image
    
    
    @classmethod
    def from_pil(cls, pil_image):
        """
        Convert a :mod:`PIL` image to a PDFium bitmap.
        Due to the restricted number of color formats and bit depths supported by PDFium's
        bitmap implementation, this may be a lossy operation.
        
        Parameters:
            pil_image (PIL.Image.Image):
                The image.
        Returns:
            PdfBitmap: PDFium bitmap (with a copy of the PIL image's data).
        """
        
        if pil_image.mode in pdfium_i.BitmapStrToConst:
            # PIL apparently always represents BGR(A/X) as RGB(A/X), so this code passage is only hit for L
            format = pdfium_i.BitmapStrToConst[pil_image.mode]
        else:
            pil_image = _pil_convert_for_pdfium(pil_image)
            format = pdfium_i.BitmapStrReverseToConst[pil_image.mode]
        
        # FIXME PIL does not seem to expose the actual image buffer directly?
        py_buffer = pil_image.tobytes()
        w, h = pil_image.size
        
        return cls.new_native(w, h, format, rev_byteorder=False, buffer=py_buffer)
    
    
    # TODO implement from_numpy()


def _pil_convert_for_pdfium(pil_image):
    
    # FIXME? convoluted / hard to understand; improve control flow
    
    if pil_image.mode == "1":
        pil_image = pil_image.convert("L")
    elif pil_image.mode.startswith("RGB"):
        pass
    elif "A" in pil_image.mode:
        pil_image = pil_image.convert("RGBA")
    else:
        pil_image = pil_image.convert("RGB")
    
    # convert RGB(A/X) to BGR(A) for PDFium
    if pil_image.mode == "RGB":
        r, g, b = pil_image.split()
        pil_image = PIL.Image.merge("RGB", (b, g, r))
    elif pil_image.mode == "RGBA":
        r, g, b, a = pil_image.split()
        pil_image = PIL.Image.merge("RGBA", (b, g, r, a))
    elif pil_image.mode == "RGBX":
        # technically the x channel may be unnecessary, but preserve what the caller passes in
        r, g, b, x = pil_image.split()
        pil_image = PIL.Image.merge("RGBX", (b, g, r, x))
    
    return pil_image
