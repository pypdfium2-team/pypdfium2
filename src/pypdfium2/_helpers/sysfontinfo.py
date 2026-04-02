# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PdfSysfontBase", "PdfSysfontListener", "PdfDefaultSysfontInfo")

import sys
import ctypes
import atexit
import logging
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i
from pypdfium2._helpers.misc import PdfiumError
from pypdfium2._lazy import cached_property, cached_property_clear
FPDF_SYSFONTINFO = pdfium_c.FPDF_SYSFONTINFO

logger = logging.getLogger(__name__)


class _PdfDefaultSysfontInfoClass (pdfium_i.AutoCastable):
    
    def __init__(self):
        self._is_loaded = False
    
    @cached_property
    def raw(self):
        self._is_loaded = True
        logger.debug("Load default sysfont info")
        default_ptr = pdfium_c.FPDF_GetDefaultSystemFontInfo()
        if not default_ptr:
            raise PdfiumError(f"No default FPDF_SYSFONTINFO available on this platform ({sys.platform!r}), cannot use {type(self).__name__}.")
        # trust in python to invoke exit handlers in reverse order to creation
        # this goes before any PdfSysfontBase atexit.register(), so it should only ever be closed after the sysfontinfo which relies on this default to remain valid
        atexit.register(self._close_impl)
        return default_ptr.contents
    
    def _close_impl(self):
        if not self._is_loaded:
            return
        pdfium_i._debug_close("Free default sysfont info")
        pdfium_c.FPDF_FreeDefaultSystemFontInfo(self.raw)
        cached_property_clear(self, "raw")
        self._is_loaded = False
    
    def close(self):
        atexit.unregister(self._close_impl)
        self._close_impl()

PdfDefaultSysfontInfo = _PdfDefaultSysfontInfoClass()


class PdfSysfontBase (pdfium_i.AutoCastable):
    """
    Base helper class to create a ``FPDF_SYSFONTINFO`` callback system.
    Callbacks can be implemented by subclassing (names from ``FPDF_SYSFONTINFO``, converted to snake_case).
    When a callback is not implemented, it will be automatically delegated to the default handler.
    
    The constructor merely creates the underlying ``FPDF_SYSFONTINFO``.
    Call :meth:`.setup` to actually register it with pdfium.
    
    Parameters:
        default (PdfSysfontBase | FPDF_SYSFONTINFO):
            TODO
    
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
    
    def __init__(self, default=None, reusable=False):
        
        self._is_installed = False
        self._reusable = reusable
        self._destroyed = False
        self._child = None
        
        if default is None:
            self._owns_pdfium_default = True
            self.default = PdfDefaultSysfontInfo.raw
        else:
            self._owns_pdfium_default = False
            if isinstance(default, PdfSysfontBase):
                self._child = default
                # transfer ownership of the default instance
                self._owns_pdfium_default = self._child._owns_pdfium_default
                self._child._owns_pdfium_default = False
                default = default.raw  # resolve
            elif isinstance(default, _PdfDefaultSysfontInfoClass):
                default = default.raw
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
        
        # trust in python to keep any object members (self.raw, self.default) alive while the object itself is referenced
        # note that the object may still be needed after it was closed if reusable=True has been set and it is being wrapped by another sysfont handler
    
    def _iterkids(self):
        child = self._child
        while child:
            yield child
            child = child._child
    
    def setup(self):
        """
        Install (activate) the sysfont handler.
        
        Note:\n
            Once this method has been called, the instance is (by default) kept alive until the end of session, through an exit handler.
            To stop the sysfont handler earlier, call :meth:`.close`.\n
            Sysfont handlers are singleton, i.e. only one handler can be active at a time.
            When a new handler is installed, the previous handler (if any) is implicitly closed.
        """
        
        if PdfSysfontBase._SINGLETON is not None:
            logger.info(f"Installing a new {type(self).__name__} instance implicitly closes previous sysfont handler instance {PdfSysfontBase._SINGLETON}")
            PdfSysfontBase._SINGLETON.close(reusable=True)
        
        if any(h._destroyed for h in (self, *self._iterkids())):
            raise PdfiumError("You cannot register a sysfontinfo that has been destroyed, whether directly or indirectly. Pass `reusable=True` on construction or closing of handlers as necessary. Singleton replacement can do this implicitly.")
        
        pdfium_c.FPDF_SetSystemFontInfo(self.raw)
        PdfSysfontBase._SINGLETON = self
        self._is_installed = True
        atexit.register(self._close_impl)
    
    
    def _close_impl(self):
        
        if not self._is_installed:
            return
        
        pdfium_i._debug_close(f"Close sysfontinfo")
        
        # propagate parent state across all children, direct or indirect
        for child in self._iterkids():
            child._reusable = self._reusable
        
        # important: unsetting the sysfontinfo implies self.default.Release(), so default can only be closed after (not before!) this call
        pdfium_c.FPDF_SetSystemFontInfo(None)
        # When the object is not reusable and we have ownership of the default instance, release it.
        if not self._reusable and self._owns_pdfium_default:
            PdfDefaultSysfontInfo.close()
            self._owns_pdfium_default = False
        
        PdfSysfontBase._SINGLETON = None
    
    def close(self, reusable=None):  # manual
        """
        Manually close the sysfont handler.
        This unregisters the exit handler and releases the sysfont handler immediately.
        
        See the note above for how sysfont handler lifetime is managed by default.
        """
        if reusable is not None:
            self._reusable = reusable
        atexit.unregister(self._close_impl)
        self._close_impl()
    
    
    def _get_callback(self, c_name, py_name):
        impl = getattr(self, py_name, None)
        if not impl:
            def impl(_, *args):
                return getattr(self.default, c_name)(self.default, *args)
        return impl
    
    def release(self, _):
        if self._reusable:
            pdfium_i._debug_close(f"fontinfo::Release: skip because it is reusable")
            return
        pdfium_i._debug_close(f"fontinfo::Release: actually release (wrapped={self._child})")
        self._destroyed = True
        return self.default.Release(self.default)


class PdfSysfontListener (PdfSysfontBase):
    """
    TODO
    """
    
    def __init__(self, default=None, reusable=False, log_all=True):
        if log_all:
            self._get_callback = self._get_callback_impl
        logger.debug("Installing sysfontinfo...")
        super().__init__(default, reusable)
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
