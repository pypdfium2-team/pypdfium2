# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import logging
import ctypes
import weakref
import pypdfium2._pypdfium as pdfium
from pypdfium2._helpers.misc import (
    colour_tohex,
    BitmapTypeToNChannels,
    BitmapTypeToStr,
    BitmapTypeToStrReverse,
)

logger = logging.getLogger(__name__)

try:
    import PIL.Image
except ImportError:
    PIL = None

try:
    import numpy
except ImportError:
    numpy = None


class PdfBitmapInfo:
    """
    Complementary information accompanying a bitmap buffer.
    
    Attributes:
        format (int):
            PDFium pixel format constant (:data:`FPDFBitmap_*`)
        n_channels (int):
            Number of channels per pixel (e. g. 4 for BGRA, 3 for BGR).
        width (int):
            Width of the bitmap (horizontal size).
        height (int):
            Height of the bitmap (vertical size).
        stride (int):
            Number of bytes per line in the buffer.
            Depending on how the bitmap was created, there may be a padding of unused bytes at the end of each line, so this value can be greater than ``width * n_channels``.
        rev_byteorder (bool):
            Whether the byte order of the pixel data is reversed (i. e. ``RGB(A/X)`` instead of ``BGR(A/X)``).
    """
    
    def __init__(
            self,
            format,
            n_channels,
            width,
            height,
            stride,
            rev_byteorder,
        ):
        self.format = format
        self.n_channels = n_channels
        self.width = width
        self.height = height
        self.stride = stride
        self.rev_byteorder = rev_byteorder
    
    # TODO consider changing to attribute? This is something very basic.
    def get_mode(self):
        """
        .. _PIL Modes: https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-modes
        
        Returns:
            str: The bitmap format as string (see `PIL Modes`_).
        """
        if self.rev_byteorder:
            return BitmapTypeToStrReverse[self.format]
        else:
            return BitmapTypeToStr[self.format]


class PdfBitmap:
    """
    Bitmap helper class.
    
    Hint:
        This class provides built-in converters (including :meth:`.to_pil`, :meth:`.to_numpy`) that may be used to create a different representation of the bitmap.
        Converters can be applied on :class:`.PdfBitmap` objects either as bound method (``bitmap.to_*()``), or as function (``PdfBitmap.to_*(bitmap)``)
        The second pattern is useful for API methods that need to apply a caller-provided converter (e. g. :meth:`.PdfDocument.render`)
    
    Attributes:
        raw (FPDF_BITMAP):
            The underlying PDFium bitmap handle.
        buffer (ctypes.c_ubyte):
            A ctypes array representation of the pixel data (each item is an unsigned byte, i. e. a number ranging from 0 to 255).
        info (PdfBitmapInfo):
            Accompanying bitmap information (pixel format, size, ...).
    """
    
    def __init__(
            self,
            raw,
            buffer,
            info,
            needs_free,
        ):
        
        self.raw = raw
        self.buffer = buffer
        self.info = info
        
        self._finalizer = None
        if needs_free:
            self._finalizer = weakref.finalize(self.buffer, self._static_close, self.raw)
    
    @staticmethod
    def _static_close(raw):
        # logger.debug("Closing bitmap")
        pdfium.FPDFBitmap_Destroy(raw)
    
    
    @classmethod
    def new_native(cls, width, height, format, rev_byteorder=False):
        """
        Create a new bitmap using :func:`FPDFBitmap_CreateEx`, with a buffer allocated by Python/ctypes.
        Refer to :class:`.PdfBitmapInfo` for parameter documentation.
        
        Bitmaps created by this function are always packed (no unused bytes at line end).
        """
        
        n_channels = BitmapTypeToNChannels[format]
        stride = width * n_channels
        total_bytes = stride * height
        buffer = (ctypes.c_ubyte * total_bytes)()
        raw = pdfium.FPDFBitmap_CreateEx(width, height, format, buffer, stride)
        
        # alternatively, we could call the constructor directly with the information from above
        return cls.from_raw(raw, rev_byteorder, buffer)
    
    
    @classmethod
    def new_foreign(cls, width, height, format, rev_byteorder=False, force_packed=False):
        """
        Create a new bitmap using :func:`FPDFBitmap_CreateEx`, with a buffer allocated by PDFium.
        
        Using this method is discouraged. Prefer :meth:`.new_native` instead.
        
        Parameters:
            force_packed (bool):
                Whether to force the creation of a packed bitmap, where ``stride == width * n_channels``. [#force-packed]_
                Otherwise, there may be a padding of unused bytes at line end.
        
        .. [#force-packed] Note, though, that this would pass a stride value to PDFium without providing an external buffer. Strictly speaking, this is not officially approved by PDFium's documentation.
        """
        
        if force_packed:
            stride = width * BitmapTypeToNChannels[format]
        else:
            stride = 0
        
        raw = pdfium.FPDFBitmap_CreateEx(width, height, format, None, stride)
        return cls.from_raw(raw, rev_byteorder)
    
    
    @classmethod
    def new_foreign_simple(cls, width, height, use_alpha, rev_byteorder=False):
        """
        Create a new bitmap using :func:`FPDFBitmap_Create`. The buffer is allocated by PDFium.
        The resulting bitmap is supposed to be packed (i. e. no gap of unused bytes between lines).
        
        Using this method is discouraged. Prefer :meth:`.new_native` instead.
        
        Parameters:
            use_alpha (bool):
                Indicate whether the alpha channel is used.
                If :data:`True`, the pixel format will be BGRA. Otherwise, it will be BGRX.
        """
        raw = pdfium.FPDFBitmap_Create(width, height, use_alpha)
        return cls.from_raw(raw, rev_byteorder)
    
    
    @classmethod
    def from_raw(cls, raw, rev_byteorder=False, ex_buffer=None):
        """
        Construct a :class:`.PdfBitmap` wrapper around a raw PDFium bitmap handle.
        
        Parameters:
            raw (FPDF_BITMAP):
                PDFium bitmap handle.
            rev_byteorder (bool):
                Whether the bitmap uses reverse byte order.
            ex_buffer (ctypes.c_ubyte | None):
                If the bitmap was created from a buffer allocated by Python/ctypes, pass in the ctypes array to keep it referenced.
        """
        
        width = pdfium.FPDFBitmap_GetWidth(raw)
        height = pdfium.FPDFBitmap_GetHeight(raw)
        format = pdfium.FPDFBitmap_GetFormat(raw)
        n_channels = BitmapTypeToNChannels[format]
        stride = pdfium.FPDFBitmap_GetStride(raw)
        
        if ex_buffer is None:
            needs_free = True
            total_bytes = stride * height
            first_item = pdfium.FPDFBitmap_GetBuffer(raw)
            buffer_ptr = ctypes.cast(first_item, ctypes.POINTER(ctypes.c_ubyte * total_bytes))
            buffer = buffer_ptr.contents
        else:
            needs_free = False
            buffer = ex_buffer
        
        info = PdfBitmapInfo(
            format = format,
            n_channels = n_channels,
            width = width,
            height = height,
            stride = stride,
            rev_byteorder = rev_byteorder,
        )
        return cls(
            raw = raw,
            buffer = buffer,
            info = info,
            needs_free = needs_free,
        )
    
    
    def fill_rect(self, left, top, width, height, colour):
        """
        Fill a rectangle on the bitmap with the given colour.
        The coordinate system starts at the top left corner of the image.
        
        Note:
            This function replaces the colour values in the given rectangle. It does not perform alpha compositing.
        
        Parameters:
            colour (typing.Tuple[int, int, int, int]):
                RGBA fill colour (a tuple of 4 integers ranging from 0 to 255).
        """
        c_colour = colour_tohex(colour, self.info.rev_byteorder)
        pdfium.FPDFBitmap_FillRect(self.raw, left, top, width, height, c_colour)
    
    
    # Assumption: If the result is a view of the buffer, it holds a reference to said buffer (directly or indirectly), so that a possible finalizer is not called prematurely. This seems to hold true for numpy and PIL.
    
    def to_numpy(self):
        """
        *Requires* :mod:`numpy`.
        
        Convert the bitmap to a NumPy array.
        
        The array contains as many rows as the bitmap is high.
        Each row contains as many pixels as the bitmap is wide.
        The length of each pixel corresponds to the number of channels.
        
        The resulting array is supposed to share memory with the original bitmap buffer, so changes to the buffer should be reflected in the array, and vice versa.
        
        This converter takes :attr:`~.PdfBitmapInfo.stride` into account.
        
        Returns:
            numpy.ndarray: NumPy array representation of the bitmap.
        """
        
        # https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html#numpy.ndarray
        
        if numpy is None:
            raise RuntimeError("NumPy library needs to be installed for to_numpy() converter.")
        
        info = self.info
        array = numpy.ndarray(
            # layout: row major
            shape = (info.height, info.width, info.n_channels),
            dtype = ctypes.c_ubyte,
            buffer = self.buffer,
            # number of bytes per item for each nesting level (outer->inner, i. e. row, pixel, value)
            strides = (info.stride, info.n_channels, 1),
        )
        
        return array
    
    
    def to_pil(self):
        """
        *Requires* :mod:`PIL`.
        
        Convert the bitmap to a PIL image, using :func:`PIL.Image.frombuffer`.
        
        For ``RGBA``, ``RGBX`` and ``L`` buffers, PIL is supposed to share memory with the original bitmap buffer, so changes to the buffer should be reflected in the image. Otherwise, PIL will make a copy of the data.
        
        This converter takes :attr:`~.PdfBitmapInfo.stride` into account.
        
        Returns:
            PIL.Image.Image: PIL image representation of the bitmap.
        """
        
        # https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.frombuffer
        # https://pillow.readthedocs.io/en/stable/handbook/writing-your-own-image-plugin.html#the-raw-decoder
        
        if PIL is None:
            raise RuntimeError("Pillow library needs to be installed for to_pil() converter.")
        
        info = self.info
        src_mode = info.get_mode()
        dest_mode = BitmapTypeToStrReverse[info.format]
        
        image = PIL.Image.frombuffer(
            dest_mode,                  # target colour format
            (info.width, info.height),  # size
            self.buffer,                # buffer
            "raw",                      # decoder
            src_mode,                   # input colour format
            info.stride,                # bytes per line
            1,                          # orientation (top->bottom)
        )
        
        return image
