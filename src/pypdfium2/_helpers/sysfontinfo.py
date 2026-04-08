# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PdfSysfontBase", )

import sys
import atexit
import logging
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i
from pypdfium2._helpers.misc import PdfiumError
from pypdfium2._lazy import cached_property, cached_property_clear

logger = logging.getLogger(__name__)


class _DefaultSysfontInfoClass:
    
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

_DefaultSysfontInfo = _DefaultSysfontInfoClass()

_CallbackNames = ("Release", "EnumFonts", "MapFont", "GetFont", "GetFontData", "GetFaceName", "GetFontCharset", "DeleteFont")


class PdfSysfontBase (pdfium_i.AutoCastable):
    """
    Base helper class to create a ``FPDF_SYSFONTINFO`` callback system.
    Callbacks can be implemented by subclassing (see `fpdf_sysfontinfo.h` for available callouts and documentation).
    
    This constructor merely creates the underlying ``FPDF_SYSFONTINFO`` instance.
    Call :meth:`.setup` to actually register it with pdfium.
    
    System font handlers may wrap another implementation, by default the root implementation provided by pdfium.
    When a callback is not implemented, it will be automatically delegated to the default handler.
    See the example below for how to invoke the default handler in a callback:
    
    .. code-block:: python
        
        class MySysfontImpl (PdfSysfontBase):
            # substitute CallbackName accordingly
            def CallbackName(self, _, arg1, arg2, ...)
                print("Wrap before")
                # Important: Do not pass the _ argument here, that's a pointer to self.raw.
                # Pass self.default instead. The C callback expects its own struct, not the wrapper.
                out = self.default.CallbackName(self.default, arg1, arg2, ...)
                print("Wrap after")
                return out
    
    Alternatively, if using subclassing, you may want\n
    .. code-block:: python\n
        out = super().CallbackName(_, arg1, arg2, ...)\n
    when the next class in the MRO has an implementation that you want to call.
    
    Parameters:
        default (None | FPDF_SYSFONTINFO | PdfSysfontBase):
            The sysfont handler to be wrapped. If None (the default), pdfium's root implementation will be used.
            Otherwise, this can be either a raw ``FPDF_SYSFONTINFO`` or another :class:`.PdfSysfontBase` instance.
    
    Note:
        When another :class:`.PdfSysfontBase` is being wrapped, some tricks are applied to avoid overhead:\n
        - Where wrapper and child share the same callback, the child method will be forwarded to the wrapper (so, as a side effect, even stacking instances of the same class would result in only one call).
        - Also, only in the actual ``FPDF_SYSFONTINFO`` object are callbacks ever enclosed in their :func:`~ctypes.CFUNCTYPE`, whereas wrappers call the original function directly.
    
    Attributes:
        raw (FPDF_SYSFONTINFO):
            The underlying ``FPDF_SYSFONTINFO`` interface struct implemented by this class. May wrap :attr:`.default`.
        default (FPDF_SYSFONTINFO | PdfSysfontBase):
            The sysfont handler being wrapped. Wrapper callbacks typically delegate the actual work to the default implementation.
        version (int):
            The ``FPDF_SYSFONTINFO`` struct version used. Matches :attr:`.default.version` and :attr:`.raw.version`.
            This is provided for interface compatibility with ``FPDF_SYSFONTINFO``, so that :attr:`.default` can be either a raw struct or :class:`.PdfSysfontBase`.
    """
    
    #: PdfSysfontBase | None: Currently registered sysfont handler, or None if no sysfont handler is installed. This is a class-level attribute.
    SINGLETON = None
    
    def __init__(self, default=None):
        
        self._is_installed = False
        self._reusable = None
        self._destroyed = False
        self._child = None
        
        if default is None:
            self.default = _DefaultSysfontInfo.raw
        else:
            self.default = default
            if isinstance(self.default, PdfSysfontBase):
                self._child = self.default
                self._forward_default_callbacks()
        
        self.version = self.default.version
        self.raw = pdfium_c.FPDF_SYSFONTINFO()
        self.raw.version = self.version
        
        callbacks = {n: getattr(self, n) for n in _CallbackNames}
        if self.version != 1:  # as per docs
            del callbacks["EnumFonts"]
        pdfium_i.set_callbacks(self.raw, **callbacks)
    
    
    def _forward_default_callbacks(self):
        # for any callbacks that were not re-implemented, we forward from default to avoid needless python function calls
        reference_class = type(self)  # or really just PdfSysfontBase?
        for cb_name in _CallbackNames:
            candidate = getattr(self.default, cb_name)
            if getattr(reference_class, cb_name) is candidate.__func__:
                setattr(self, cb_name, candidate)
    
    def _iterkids(self):
        child = self._child
        while child:
            yield child
            child = child._child
    
    def setup(self, reusable=False):
        """
        Install (activate) the sysfont handler.
        
        Note:\n
            Once this method has been called, the instance is (by default) kept alive until the end of session, through an exit handler.
            To stop the sysfont handler earlier, call :meth:`.close`.\n
            Sysfont handlers are singleton, i.e. only one handler can be active at a time.
            When a new handler is installed, the previous handler (if any) is implicitly closed.
        """
        
        if PdfSysfontBase.SINGLETON is not None:
            logger.info(f"Installing a new {type(self).__name__} instance implicitly closes previous sysfont handler instance {PdfSysfontBase.SINGLETON}")
            PdfSysfontBase.SINGLETON.close(reusable=True)
        
        if any(h._destroyed for h in (self, *self._iterkids())):
            raise PdfiumError("You cannot register a sysfontinfo that has been destroyed, whether directly or indirectly. Pass `reusable=True` on setup or closing of handlers as necessary. Singleton replacement can do this implicitly.")
        
        # trust in python to keep any object members (self.raw, self.default) alive while the object itself is referenced
        # note that the object may still be needed after it was closed if reusable=True has been set and it is being wrapped by another sysfont handler
        pdfium_c.FPDF_SetSystemFontInfo(self.raw)
        PdfSysfontBase.SINGLETON = self
        self._is_installed = True
        self._reusable = reusable
        atexit.register(self._close_impl)
    
    
    def _close_impl(self):
        if not self._is_installed:
            return
        pdfium_i._debug_close(f"Close sysfontinfo")
        
        # propagate parent state across all children, direct or indirect
        for child in self._iterkids():
            child._reusable = self._reusable
        
        pdfium_c.FPDF_SetSystemFontInfo(None)
        if self._destroyed:
            # Assuming pdfium's default impl was used. In the unlikely event that it was not used, this is a no-op.
            _DefaultSysfontInfo.close()
        PdfSysfontBase.SINGLETON = None
    
    def close(self, reusable=None):  # manual
        """
        Manually close the sysfont handler.
        This unregisters the exit handler and releases the sysfont handler immediately.
        
        See the note above for how sysfont handler lifetime is managed by default.
        
        Parameters:
            reusable (bool):
                If False (the default), closing will destroy pdfium's default handler, rendering any direct or indirect wrappers thereof unusable.
                If True, however, the default handler will not be harmed, so the object can be reused, like re-installing it some time after closing, wrapping it in another object, or just preserving the default handler for a new :class:`.PdfSysfontBase` instance.
                This is automatically set to True on singleton replacement, when the previous handler is implicitly closed (i.e. ownership of the default instance is transferred to the new handler).
        """
        if reusable is not None:
            self._reusable = reusable
        atexit.unregister(self._close_impl)
        self._close_impl()
    
    def Release(self, _):
        if self._reusable:
            pdfium_i._debug_close(f"fontinfo::Release: skip because it is reusable")
            return
        pdfium_i._debug_close(f"fontinfo::Release: actually release (wrapped={self._child})")
        self._destroyed = True
        return self.default.Release(self.default)
    
    def EnumFonts(self, _, pMapper):
        return self.default.EnumFonts(self.default, pMapper)
    
    def MapFont(self, _, weight, bItalic, charset, pitch_family, face, _ignored):
        return self.default.MapFont(self.default, weight, bItalic, charset, pitch_family, face, _ignored)
    
    def GetFont(self, _, face):
        return self.default.GetFont(self.default, face)
    
    def GetFontData(self, _, hFont, table, buffer, buf_size):
        return self.default.GetFontData(self.default, hFont, table, buffer, buf_size)
    
    def GetFaceName(self, _, hFont, buffer, buf_size):
        return self.default.GetFaceName(self.default, hFont, buffer, buf_size)
    
    def GetFontCharset(self, _, hFont):
        return self.default.GetFontCharset(self.default, hFont)
    
    def DeleteFont(self, _, hFont):
        return self.default.DeleteFont(self.default, hFont)
