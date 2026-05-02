# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
import logging
from contextlib import contextmanager
import pypdfium2._helpers as pdfium
import pypdfium2.internal as pdfium_i

logger = logging.getLogger("pypdfium2_cli")

@contextmanager
def _tmp_loglevel_ctx(logger, level):
    _orig_loglevel = logger.getEffectiveLevel()
    logger.setLevel(level)
    try:
        yield
    finally:
        logger.setLevel(_orig_loglevel)

@contextmanager
def _noop_ctx():
    yield


class PdfSysfontListener (pdfium.PdfSysfontBase):
    
    def __init__(self, default=None):
        logger.debug("Installing sysfontinfo...")
        super().__init__(default)
        logger.debug(f"fontinfo default interface version is {self.version}")
    
    def setup(self, *args, tmp_loglevel=logging.INFO, **kwargs):
        # NOTE this will still do the work (i.e. get strings, map flags and create the log string), just mask the actual logging
        ctx = _noop_ctx() if tmp_loglevel is None else _tmp_loglevel_ctx(logger, tmp_loglevel)
        with ctx:
            super().setup(*args, **kwargs)
    
    def MapFont(self, _, weight, bItalic, charset, pitch_family, face, _ignored):
        face_bstr = ctypes.cast(face, ctypes.c_char_p).value
        logger.debug(f"fontinfo::MapFont:in (weight={weight}, bItalic={bool(bItalic)}, charset={pdfium_i.CharsetToStr.get(charset)!r}, pitch_family={pdfium_i.PdfFontPitchFamilyFlags(pitch_family).name!r}, face={face_bstr!r})")
        out = self.default.MapFont(self.default, weight, bItalic, charset, pitch_family, face, _ignored)
        # For internal substitution, check the family names in `pypdfium2 fonts` CLI output.
        # If you see names like "Chrom Sans OTF" or "Chrom Serif OTF" then you probably got internal substitution.
        vis_out = out or f"{out} (maybe internal substitution)"
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
        logger.debug(f"fontinfo::GetFontCharset {hFont, }")
        return self.default.GetFontCharset(self.default, hFont)
    
    def DeleteFont(self, _, hFont):
        logger.debug(f"fontinfo::DeleteFont {hFont, }")
        return self.default.DeleteFont(self.default, hFont)
