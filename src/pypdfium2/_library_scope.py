# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import atexit
import logging
import pypdfium2.raw as pdfium_c
from pypdfium2.internal import bases
from pypdfium2_cfg import DEBUG_AUTOCLOSE

logger = logging.getLogger("pypdfium2")


def init_lib():
    assert not bases.LIBRARY_AVAILABLE
    if DEBUG_AUTOCLOSE:  # pragma: no cover
        logger.debug("Initialize PDFium")
    
    # PDFium init API may change in the future: https://crbug.com/pdfium/1446
    # NOTE Technically, FPDF_InitLibrary() would be sufficient for our purposes, but pdfium docs say "This will be deprecated in the future", so don't use it to be on the safe side. Also, avoid experimental config versions that might not be promoted to stable.
    config = pdfium_c.FPDF_LIBRARY_CONFIG(
        version = 2,
        m_pUserFontPaths = None,
        m_pIsolate = None,
        m_v8EmbedderSlot = 0,
        # m_pPlatform = None,  # v3
        # m_RendererType = pdfium_c.FPDF_RENDERERTYPE_AGG,  # v4
    )
    pdfium_c.FPDF_InitLibraryWithConfig(config)
    bases.LIBRARY_AVAILABLE = True


def _close_objects():
    for cls, obj_wrefs in bases.ObjectTracker.items():
        # pdfium_i._debug_close(f"{cls and cls.__name__}: {obj_wrefs}")
        # retain copy() as an extra precaution for now
        for wref in obj_wrefs.copy():
            obj = wref()
            if obj is None:
                bases._warn_close(f"Weakref {wref} was not cleaned up from ObjectTracker?")
            else:
                bases._warn_close(f"The following object was still open and will be closed now: {obj}")
                obj.close()
        obj_wrefs.clear()


def destroy_lib():  # pragma: no cover
    assert bases.LIBRARY_AVAILABLE
    bases.REMOVE_FROM_TRACKER = False
    try:
        _close_objects()
    finally:
        bases.REMOVE_FROM_TRACKER = True
        bases._debug_close("Destroy PDFium")
        pdfium_c.FPDF_DestroyLibrary()
        bases.LIBRARY_AVAILABLE = False


# Load pdfium
init_lib()

# Register an exit handler that will free pdfium
atexit.register(destroy_lib)
