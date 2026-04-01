# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PdfSysfontBase", "PdfSysfontListener")

import sys
import ctypes
import atexit
import locale
import logging
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
        
        self._is_installed = False
        self._destroys_default = False
        if default is None:
            self._made_default = True
            self.default = self._get_default()
        else:
            self._made_default = False
            if isinstance(default, PdfSysfontBase):
                assert not default._destroys_default, "When a sysfontinfo is nested, it must not destroy its default."
                assert default.default is not None, "Cannot use a closed sysfont handler whose default has been freed."
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
        atexit.register(self._close_impl)
    
    
    def _get_default(self):
        default_ptr = pdfium_c.FPDF_GetDefaultSystemFontInfo()
        if not default_ptr:
            raise PdfiumError(f"No default FPDF_SYSFONTINFO available on this platform ({sys.platform!r}), cannot use {type(self).__name__}.")
        return default_ptr.contents
    
    
    def setup(self):
        if PdfSysfontBase._SINGLETON is self:
            return
        if self._made_default and self.default is None:
            self.default = self._get_default()
        self._is_installed = True
        self._destroys_default = self._made_default
        atexit.unregister(self._close_impl)
        atexit.register(self._close_impl)
        if PdfSysfontBase._SINGLETON is not None:
            logger.info(f"Constructing a new {type(self).__name__} instance implicitly closes previous sysfont handler instance {PdfSysfontBase._SINGLETON}")
            PdfSysfontBase._SINGLETON.close()
        pdfium_c.FPDF_SetSystemFontInfo(self.raw)
        PdfSysfontBase._SINGLETON = self
    
    
    def _close_impl(self):
        
        id(self.raw)
        id(self.default)
        
        if self._is_installed:
            # this calls self.default.Release, so the default handler must be freed after (not before!) this call
            pdfium_i._debug_close(f"Unset sysfontinfo")
            pdfium_c.FPDF_SetSystemFontInfo(None)
            self._is_installed = False
            PdfSysfontBase._SINGLETON = None
        if self._destroys_default:
            pdfium_i._debug_close(f"Close default sysfontinfo")
            self._destroys_default = False
            default = self.default
            self.default = None
            pdfium_c.FPDF_FreeDefaultSystemFontInfo(default)
    
    def close(self):  # manual
        """
        Manually close the sysfont handler.
        This unregisters the exit handler and releases the sysfont handler immediately.
        
        See the note above for how sysfont handler lifetime is managed by default.
        """
        atexit.unregister(self._close_impl)
        self._close_impl()
    
    
    def _get_callback(self, c_name, py_name):
        impl = getattr(self, py_name, None)
        if not impl:
            def impl(_, *args):
                return getattr(self.default, c_name)(self.default, *args)
        return impl
    
    def release(self, _):
        if not self._destroys_default:
            return
        pdfium_i._debug_close("fontinfo::Release")
        return self.default.Release(self.default)


class PdfSysfontListener (PdfSysfontBase):
    """
    Sysfont listener that wraps the default system font info, intercepting callbacks
    to track which fonts PDFium requests and whether they were found on the system.

    Use :meth:`get_font_requests` to retrieve the accumulated results, and
    :meth:`clear_font_requests` to reset the log.
    """

    def __init__(self, default=None, log_all=True):
        self._font_requests = {}
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

    def _record_request(self, face, result):
        face_bstr = ctypes.cast(face, ctypes.c_char_p).value
        if face_bstr:
            name = face_bstr.decode(locale.getpreferredencoding(False), errors="replace")
            if not self._font_requests.get(name, False):
                self._font_requests[name] = bool(result)

    def get_font_requests(self):
        """
        Return the accumulated font resolution log.

        Returns:
            dict[str, bool]:
                Maps each font name (as requested by PDFium) to a boolean
                indicating whether the font was found on the system.
        """
        return dict(self._font_requests)

    def clear_font_requests(self):
        """Clear the accumulated font resolution log."""
        self._font_requests.clear()

    def map_font(self, _, weight, bItalic, charset, pitch_family, face, bExact):
        face_bstr = ctypes.cast(face, ctypes.c_char_p).value
        logger.debug(f"fontinfo::MapFont:in (weight={weight}, bItalic={bool(bItalic)}, charset={pdfium_i.CharsetToStr.get(charset)!r}, pitch_family={pdfium_i.PdfFontPitchFamilyFlags(pitch_family).name!r}, face={face_bstr!r})")
        out = self.default.MapFont(self.default, weight, bItalic, charset, pitch_family, face, bExact)
        logger.debug(f"fontinfo::MapFont:out {out}")
        self._record_request(face, out)
        return out

    def get_font(self, _, face):
        face_bstr = ctypes.cast(face, ctypes.c_char_p).value
        logger.debug(f"fontinfo::GetFont:in (face={face_bstr!r})")
        out = self.default.GetFont(self.default, face)
        logger.debug(f"fontinfo::GetFont:out {out}")
        self._record_request(face, out)
        return out

    # def enum_fonts(self, _, pMapper):
    #     # pMapper: opaque pointer to internal font mapper, used when calling FPDF_AddInstalledFont()
    #     # note, we don't actually call FPDF_AddInstalledFont() as we call the default EnumFont, impl assuming this suffices.
    #     logger.debug(f"fontinfo::EnumFonts {pMapper, }")
    #     return self.default.EnumFonts(self.default, pMapper)

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
