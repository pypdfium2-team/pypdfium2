# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PdfSysfontBase", "PdfSysfontListener")

import sys
import atexit
import logging
import pypdfium2.raw as pdfium_c
from pypdfium2._helpers.misc import PdfiumError
import pypdfium2.internal as pdfium_i
FPDF_SYSFONTINFO = pdfium_c.FPDF_SYSFONTINFO

logger = logging.getLogger(__name__)


class PdfSysfontBase:
    """
    Base helper class to set up and register a ``FPDF_SYSFONTINFO`` callback system.
    Callbacks need to be implemented by subclassing (names from ``FPDF_SYSFONTINFO``, converted to snake-case).
    
    Important:
        In subclass callbacks, you will typically want to wrap pdfium's default implementation rather than writing your own implementation from scratch.
        This class exposes the default ``FPDF_SYSFONTINFO`` instance as ``self._default``.
        Invoke default callbacks with ``self._default_ptr`` as first argument, not with the pointer to the wrapper struct recieved as first argument after ``self`` in the function signature.
    
    Note:
        When a :class:`.PdfSysfontBase` instance is created, it is (by default) kept alive until the end of the session through an exit handler.
        To stop the sysfont handler earlier, call :meth:`.close`, which will unregister the exit handler and release the sysfont handler immediately.
    """
    
    def __init__(self):
        
        self._default_ptr = pdfium_c.FPDF_GetDefaultSystemFontInfo()
        if not self._default_ptr:
            raise PdfiumError(f"No default FPDF_SYSFONTINFO available on this platform ({sys.platform!r}), cannot use {type(self).__name__}.")
        
        self._default = self._default_ptr.contents
        self._wrapper = FPDF_SYSFONTINFO()
        self._wrapper.version = self._default.version
        callbacks = dict(
            Release = self.release,
            EnumFonts = self.enum_fonts,
            MapFont = self.map_font,
            GetFont = self.get_font,
            GetFontData = self.get_font_data,
            GetFaceName = self.get_face_name,
            GetFontCharset = self.get_font_charset,
            DeleteFont = self.delete_font,
        )
        if self._default.version != 1:  # as per docs
            del callbacks["EnumFonts"]
        
        pdfium_i.set_callbacks(self._wrapper, **callbacks)
        pdfium_c.FPDF_SetSystemFontInfo(self._wrapper)
        
        atexit.register(self._close_impl)
    
    def _close_impl(self):
        id(self._wrapper)
        id(self._default)
        pdfium_c.FPDF_SetSystemFontInfo(None)
        # ^ this calls Release, so the default handler must be freed after (not before!) this call
        pdfium_c.FPDF_FreeDefaultSystemFontInfo(self._default_ptr)
    
    def close(self):  # manual
        atexit.unregister(self._close_impl)
        self._close_impl()


class PdfSysfontListener (PdfSysfontBase):
    """
    TODO
    """
    
    def __init__(self):
        super().__init__()
        logger.debug(f"fontinfo default interace version is {self._default.version}")
    
    def _close_impl(self):
        pdfium_i._safe_debug("Closing sysfontinfo...")
        super()._close_impl()
    
    def release(self, _):
        pdfium_i._safe_debug("fontinfo::Release")
        return self._default.Release(self._default_ptr)
    
    def enum_fonts(self, _, pMapper):
        logger.debug(f"fontinfo::EnumFonts {pMapper, }")
        return self._default.EnumFonts(self._default_ptr, pMapper)
    
    def map_font(self, _, weight, bItalic, charset, pitch_family, face, bExact):
        logger.debug(f"fontinfo::MapFont {weight, bItalic, charset, pitch_family, face, bExact}")
        return self._default.MapFont(self._default_ptr, weight, bItalic, charset, pitch_family, face, bExact)
    
    def get_font(self, _, face):
        logger.debug(f"fontinfo::GetFont {face, }")
        return self._default.GetFont(self._default_ptr, face)
    
    def get_font_data(self, _, hFont, table, buffer, buf_size):
        logger.debug(f"fontinfo::GetFontData {hFont, table, buffer, buf_size}")
        return self._default.GetFontData(self._default_ptr, hFont, table, buffer, buf_size)
    
    def get_face_name(self, _, hFont, buffer, buf_size):
        logger.debug(f"fontinfo::GetFaceName {hFont, buffer, buf_size}")
        return self._default.GetFaceName(self._default_ptr, hFont, buffer, buf_size)
    
    def get_font_charset(self, _, hFont):
        logger.debug(f"fontinfo::GetCharset {hFont, }")
        return self._default.GetFontCharset(self._default_ptr, hFont)
    
    def delete_font(self, _, hFont):
        logger.debug(f"fontinfo::DeleteFont {hFont, }")
        return self._default.DeleteFont(self._default_ptr, hFont)
