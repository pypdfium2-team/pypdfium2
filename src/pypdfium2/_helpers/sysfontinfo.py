# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PdfSysfontBase", "PdfSysfontListener")

import sys
import ctypes
import atexit
import logging
import pypdfium2_cfg
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i
from pypdfium2._helpers.misc import PdfiumError
FPDF_SYSFONTINFO = pdfium_c.FPDF_SYSFONTINFO

logger = logging.getLogger(__name__)


class PdfSysfontBase (pdfium_i.AutoCastable):
    """
    Base helper class to set up and register a ``FPDF_SYSFONTINFO`` callback system.
    Callbacks can be implemented by subclassing (names from ``FPDF_SYSFONTINFO``, converted to snake_case).
    When a callback is not implemented, this constructor will automatically delegate it to the default handler.
    
    Parameters:
        default (PdfSysfontBase | FPDF_SYSFONTINFO):
            TODO
    
    Note:\n
        When a :class:`.PdfSysfontBase` instance is created, it is (by default) kept alive until the end of session, through an exit handler.
        To stop the sysfont handler earlier, call :meth:`.close`.\n
        Sysfont handlers are singleton, i.e. only one handler can live at a time.
        When a new handler is created, the previous handler (if any) is implicitly closed.
    
    Important:
        In subclass callbacks, you will typically want to wrap pdfium's default implementation rather than writing your own implementation from scratch.
        This class exposes the default ``FPDF_SYSFONTINFO`` instance as ``self.default``.
        Invoke default callbacks with ``self.default`` as first argument, not with the pointer to the wrapper struct received as first argument after ``self`` in the function signature.
    
    Attributes:
        raw (FPDF_SYSFONTINFO):
            ...
        default (FPDF_SYSFONTINFO):
            ...
    """
    
    _SINGLETON = None
    
    def __init__(self, default=None):
        
        self._is_closed = False
        if default is None:
            self._own_default = True
            default_ptr = pdfium_c.FPDF_GetDefaultSystemFontInfo()
            if not default_ptr:
                raise PdfiumError(f"No default FPDF_SYSFONTINFO available on this platform ({sys.platform!r}), cannot use {type(self).__name__}.")
            self.default = default_ptr.contents
        else:
            self._own_default = False
            if isinstance(default, PdfSysfontBase):
                default = default.raw  # resolve
            self.default = default
        
        self.raw = FPDF_SYSFONTINFO()
        self.raw.version = self.default.version
        cb_names = {
            "Release": "release",
            "EnumFonts": "enum_fonts",
            "MapFont": "map_font",
            "GetFont": "get_font",
            "GetFontData": "get_font_data",
            "GetFaceName": "get_face_name",
            "GetFontCharset": "get_font_charset",
            "DeleteFont": "delete_font",
        }
        if self.default.version != 1:  # as per docs
            del cb_names["EnumFonts"]
        
        callbacks = {cn: self._get_callback(cn, pn) for cn, pn in cb_names.items()}
        pdfium_i.set_callbacks(self.raw, **callbacks)

        if PdfSysfontBase._SINGLETON is not None:
            logger.info(f"Constructing a new {type(self).__name__} instance implicitly closes previous sysfont handler instance {PdfSysfontBase._SINGLETON}")
            PdfSysfontBase._SINGLETON.close(_next_handler=self.raw)
        else:
            pdfium_c.FPDF_SetSystemFontInfo(self.raw)
        PdfSysfontBase._SINGLETON = self
        atexit.register(self._close_impl)
    
    def _close_impl(self, _next_handler=None):
        
        if self._is_closed:
            return
        
        pdfium_i._debug_close("Closing sysfontinfo...")
        
        id(self.raw)
        id(self.default)
        
        pdfium_c.FPDF_SetSystemFontInfo(_next_handler)
        # ^ this calls self.default.Release, so the default handler must be freed after (not before!) this call
        if self._own_default:
            pdfium_c.FPDF_FreeDefaultSystemFontInfo(self.default)
        
        self._is_closed = True
    
    def close(self, _next_handler=None):  # manual
        """
        Manually close the sysfont handler.
        This unregisters the exit handler and releases the sysfont handler immediately.
        
        See the note above for how sysfont handler lifetime is managed by default.
        """
        atexit.unregister(self._close_impl)
        self._close_impl(_next_handler)
    
    def _get_callback(self, c_name, py_name):
        impl = getattr(self, py_name, None)
        if not impl:
            def impl(_, *args):
                return getattr(self.default, c_name)(self.default, *args)
        return impl
    
    def release(self, _):
        pdfium_i._debug_close("fontinfo::Release")
        return self.default.Release(self.default)


class PdfSysfontListener (PdfSysfontBase):
    """
    TODO
    """
    
    def __init__(self, default=None, log_all=True):
        if log_all:
            self._get_callback = self._get_callback_impl
        logger.debug("Installing sysfontinfo...")
        super().__init__(default)
        logger.debug(f"fontinfo default interface version is {self.default.version}")
    
    def _get_callback_impl(self, c_name, py_name):
        impl = getattr(self, py_name, None)
        if not impl:
            def impl(_, *args):
                logger.debug(f"fontinfo::{c_name} {args}")
                return getattr(self.default, c_name)(self.default, *args)
        return impl
    
    def map_font(self, _, weight, bItalic, charset, pitch_family, face, bExact):
        face_bstr = ctypes.cast(face, ctypes.c_char_p).value
        logger.debug(f"fontinfo::MapFont:in (weight={weight}, bItalic={bool(bItalic)}, charset={pdfium_i.CharsetToStr.get(charset)!r}, pitch_family={pdfium_i.PdfFontPitchFamilyFlags(pitch_family).name!r}, face={face_bstr!r})")
        out = self.default.MapFont(self.default, weight, bItalic, charset, pitch_family, face, bExact)
        logger.debug(f"fontinfo::MapFont:out {out}")
        return out
    
    # def enum_fonts(self, _, pMapper):
    #     # pMapper: opaque pointer to internal font mapper, used when calling FPDF_AddInstalledFont()
    #     # note, we don't actually call FPDF_AddInstalledFont() as we call the default EnumFont, impl assuming this suffices.
    #     logger.debug(f"fontinfo::EnumFonts {pMapper, }")
    #     return self.default.EnumFonts(self.default, pMapper)
    
    # def get_font(self, _, face):
    #     logger.debug(f"fontinfo::GetFont {face, }")
    #     return self.default.GetFont(self.default, face)
    
    # def get_font_data(self, _, hFont, table, buffer, buf_size):
    #     logger.debug(f"fontinfo::GetFontData {hFont, table, buffer, buf_size}")
    #     return self.default.GetFontData(self.default, hFont, table, buffer, buf_size)
    
    # def get_face_name(self, _, hFont, buffer, buf_size):
    #     logger.debug(f"fontinfo::GetFaceName {hFont, buffer, buf_size}")
    #     return self.default.GetFaceName(self.default, hFont, buffer, buf_size)
    
    # def get_font_charset(self, _, hFont):
    #     logger.debug(f"fontinfo::GetCharset {hFont, }")
    #     return self.default.GetFontCharset(self.default, hFont)
    
    # def delete_font(self, _, hFont):
    #     logger.debug(f"fontinfo::DeleteFont {hFont, }")
    #     return self.default.DeleteFont(self.default, hFont)
