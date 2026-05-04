# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
import logging
import pypdfium2._helpers as pdfium
import pypdfium2.internal as pdfium_i

logger = logging.getLogger("pypdfium2_cli")


class PdfSysfontListener (pdfium.PdfSysfontBase):
    
    def __init__(self, default=None):
        logger.debug("Installing sysfontinfo...")
        super().__init__(default)
        logger.debug(f"fontinfo default interface version is {self.version}")
    
    def MapFont(self, _, weight, bItalic, charset, pitch_family, face, _ignored):
        face_bstr = ctypes.cast(face, ctypes.c_char_p).value
        logger.debug(f"fontinfo::MapFont:in (weight={weight}, bItalic={bool(bItalic)}, charset={pdfium_i.CharsetToStr.get(charset)!r}, pitch_family={pdfium_i.PdfFontPitchFamilyFlags(pitch_family).name!r}, face={face_bstr!r})")
        out = self.default.MapFont(self.default, weight, bItalic, charset, pitch_family, face, _ignored)
        # For internal substitution, check the family names in `pypdfium2 fonts` CLI output.
        # If you see names like "Chrom Sans OTF" or "Chrom Serif OTF" then you probably got internal substitution.
        vis_out = out or f"{out}  # probably internal subst with Chrome font"
        logger.debug(f"fontinfo::MapFont:out {vis_out}")
        return out
    
    def GetFont(self, _, face):
        face_bstr = ctypes.cast(face, ctypes.c_char_p).value
        logger.debug(f"fontinfo::GetFont {face_bstr, }")
        return self.default.GetFont(self.default, face)
    
    def GetFaceName(self, _, hFont, buffer, buf_size):
        logger.debug(f"fontinfo::GetFaceName {hFont, buffer, buf_size}")
        out = self.default.GetFaceName(self.default, hFont, buffer, buf_size)
        if buf_size > 0:
            logger.debug(f"-> {pdfium_i.get_buffer(buffer, buf_size-1).raw}")
        return out
    
    def EnumFonts(self, _, pMapper):
        logger.debug(f"fontinfo::EnumFonts {pMapper, }")
        return self.default.EnumFonts(self.default, pMapper)
    
    def GetFontData(self, _, hFont, table, buffer, buf_size):
        logger.debug(f"fontinfo::GetFontData {hFont, table, buffer, buf_size}")
        return self.default.GetFontData(self.default, hFont, table, buffer, buf_size)
    
    def GetFontCharset(self, _, hFont):
        # XXX haven't yet seen a sample that triggers GetFontCharset
        logger.debug(f"fontinfo::GetFontCharset {hFont, }")
        out = self.default.GetFontCharset(self.default, hFont)
        logger.debug(f"-> charset: {pdfium_i.CharsetToStr.get(out)!r}")
        return out
    
    def DeleteFont(self, _, hFont):
        logger.debug(f"fontinfo::DeleteFont {hFont, }")
        return self.default.DeleteFont(self.default, hFont)
