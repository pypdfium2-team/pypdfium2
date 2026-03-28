# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PdfFontListener", )

import logging
import pypdfium2.raw as pdfium_c
from pypdfium2.internal.utils import set_callback
FPDF_SYSFONTINFO = pdfium_c.FPDF_SYSFONTINFO

logger = logging.getLogger(__name__)

class PdfFontListener:
    
    def __init__(self):
        self._default_ptr = pdfium_c.FPDF_GetDefaultSystemFontInfo()
        self._default = self._default_ptr.contents
        print(f"fontinfo default interace version is {self._default.version}")  # XXX
        self._wrapper = FPDF_SYSFONTINFO()
        self._wrapper.version = self._default.version
        set_callback(self._wrapper, "Release", self.release)
        if self._default.version == 1:  # as per docs
            set_callback(self._wrapper, "EnumFonts", self.enum_fonts)
        set_callback(self._wrapper, "MapFont", self.map_font)
        set_callback(self._wrapper, "GetFont", self.get_font)
        set_callback(self._wrapper, "GetFontData", self.get_font_data)
        set_callback(self._wrapper, "GetFaceName", self.get_face_name)
        set_callback(self._wrapper, "GetFontCharset", self.get_font_charset)
        set_callback(self._wrapper, "DeleteFont", self.delete_font)
        pdfium_c.FPDF_SetSystemFontInfo(self._wrapper)

    def release(self, _):
        logger.debug("fontinfo::Release")
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
    
    def close(self):
        logger.debug("Closing sysfontinfo...")
        id(self._wrapper)
        id(self._default)
        pdfium_c.FPDF_SetSystemFontInfo(None)
        # ^ this calls Release, so the default handler must be freed after (not before!) this call
        pdfium_c.FPDF_FreeDefaultSystemFontInfo(self._default_ptr)

import atexit
print("Installing sysfontinfo...")  # XXX
listener = PdfFontListener()
atexit.register(listener.close)
