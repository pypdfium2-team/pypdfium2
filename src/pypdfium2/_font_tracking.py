# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("get_font_requests", "clear_font_requests")

import ctypes
import threading
import logging
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i

logger = logging.getLogger(__name__)

# Module-level state — kept alive for the library lifetime.
_default_info = None   # POINTER(FPDF_SYSFONTINFO) from FPDF_GetDefaultSystemFontInfo()
_wrapper = None        # Our FPDF_SYSFONTINFO struct
_cb_refs = []          # Strong refs to CFUNCTYPE objects to prevent GC
_font_requests = {}    # {font_name_str: bool_found}
_lock = threading.RLock()


def _install_font_tracking():
    """
    Install a wrapper around PDFium's default system font info to intercept
    MapFont/GetFont calls and log which fonts were found or missed.

    Must be called after FPDF_InitLibraryWithConfig(). All fallible work
    (getting default info, creating callbacks, building the wrapper) completes
    before FPDF_SetSystemFontInfo() — the point of no return.
    """
    global _default_info, _wrapper, _cb_refs, _font_requests

    # Step 1: Get a fresh default font info
    default_info = pdfium_c.FPDF_GetDefaultSystemFontInfo()
    if not default_info:
        logger.debug("FPDF_GetDefaultSystemFontInfo() returned NULL; font tracking unavailable")
        return

    default = default_info.contents

    # Step 2: Create all callback closures
    # MapFont and GetFont intercept and log; all others are pure delegation.
    # Intercepting callbacks use fail-open: delegate first, then try to log.
    # An exception in logging must never affect the delegation result.

    def _map_font(pThis, weight, italic, charset, pf, face, exact):
        result = default.MapFont(default_info, weight, italic, charset, pf, face, exact)
        try:
            if face:
                name = ctypes.string_at(face).decode("utf-8", errors="replace")
                with _lock:
                    if not _font_requests.get(name, False):
                        _font_requests[name] = bool(result)
        except Exception:
            pass
        return result

    def _get_font(pThis, face):
        result = default.GetFont(default_info, face)
        try:
            if face:
                name = ctypes.string_at(face).decode("utf-8", errors="replace")
                with _lock:
                    if not _font_requests.get(name, False):
                        _font_requests[name] = bool(result)
        except Exception:
            pass
        return result

    def _enum_fonts(pThis, mapper):
        default.EnumFonts(default_info, mapper)

    def _release(pThis):
        if default.Release:
            default.Release(default_info)

    def _get_font_data(pThis, font, table, buffer, buf_size):
        return default.GetFontData(default_info, font, table, buffer, buf_size)

    def _get_face_name(pThis, font, buffer, buf_size):
        return default.GetFaceName(default_info, font, buffer, buf_size)

    def _get_font_charset(pThis, font):
        return default.GetFontCharset(default_info, font)

    def _delete_font(pThis, font):
        default.DeleteFont(default_info, font)

    # Step 3: Build wrapper struct and assign callbacks
    wrapper = pdfium_c.FPDF_SYSFONTINFO()
    wrapper.version = default.version

    cb_refs = []
    for fname, pyfunc in [
        ("Release", _release),
        ("EnumFonts", _enum_fonts),
        ("MapFont", _map_font),
        ("GetFont", _get_font),
        ("GetFontData", _get_font_data),
        ("GetFaceName", _get_face_name),
        ("GetFontCharset", _get_font_charset),
        ("DeleteFont", _delete_font),
    ]:
        pdfium_i.set_callback(wrapper, fname, pyfunc)
        # Keep a strong ref to the ctypes callback object to prevent GC
        cb_refs.append(getattr(wrapper, fname))

    # Step 4: Assign module-level strong refs (before point of no return)
    _default_info = default_info
    _wrapper = wrapper
    _cb_refs = cb_refs
    _font_requests.clear()

    # Step 5: Point of no return — install the wrapper
    pdfium_c.FPDF_SetSystemFontInfo(_wrapper)


def _reset_font_tracking():
    """
    Clear the font request log after FPDF_DestroyLibrary().

    The wrapper, default_info, and callback refs are NOT cleared here —
    they must remain alive during FPDF_DestroyLibrary() since PDFium calls
    Release during shutdown. They become inert after destroy and are left
    for process exit / GC.
    """
    with _lock:
        _font_requests.clear()


def get_font_requests():
    """
    Return the accumulated font resolution log.

    Each entry maps a font name (as requested by PDFium via MapFont/GetFont)
    to a boolean indicating whether the font was found on the system.

    Font requests are accumulated across all page loads since library init
    (or since the last call to :func:`clear_font_requests`).

    Note:
        The font names logged here are those passed to PDFium's MapFont/GetFont
        callbacks, which may differ slightly from PDF BaseFont names (e.g.,
        ``"NotoSansCJKsc"`` vs ``"NotoSansCJKsc-Regular"``). Some entries may
        be internal PDFium probes rather than fonts referenced by a specific PDF.

    Returns:
        dict[str, bool]: Mapping of font name to found status.
    """
    with _lock:
        return dict(_font_requests)


def clear_font_requests():
    """
    Clear the accumulated font resolution log.
    """
    with _lock:
        _font_requests.clear()
