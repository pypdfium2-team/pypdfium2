# SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import atexit
import os, sys
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i


def init_lib():
    assert not pdfium_i.LIBRARY_AVAILABLE
    if pdfium_i.DEBUG_AUTOCLOSE:
        print("Initialize PDFium (auto)", file=sys.stderr)
    
    # PDFium init API may change in the future: https://crbug.com/pdfium/1446
    # NOTE Technically, FPDF_InitLibrary() would be sufficient for our purposes, but since it's formally marked for deprecation, don't use it to be on the safe side. Also, avoid experimental config versions that might not be promoted to stable.
    config = pdfium_c.FPDF_LIBRARY_CONFIG(
        version = 2,
        m_pUserFontPaths = None,
        m_pIsolate = None,
        m_v8EmbedderSlot = 0,
        # m_pPlatform = None,  # v3
        # m_RendererType = pdfium_c.FPDF_RENDERERTYPE_AGG,  # v4
    )
    pdfium_c.FPDF_InitLibraryWithConfig(config)
    
    pdfium_i.LIBRARY_AVAILABLE.value = True


def destroy_lib():
    assert pdfium_i.LIBRARY_AVAILABLE
    if pdfium_i.DEBUG_AUTOCLOSE:
        # use os.write() rather than print() to avoid "reentrant call" exceptions on shutdown (see https://stackoverflow.com/q/75367828/15547292)
        os.write(sys.stderr.fileno(), b"Destroy PDFium (auto)\n")
    pdfium_c.FPDF_DestroyLibrary()
    pdfium_i.LIBRARY_AVAILABLE.value = False


# Load pdfium
init_lib()

# Register an exit handler that will free pdfium
# Trust in Python to call exit handlers only after all objects have been finalized
atexit.register(destroy_lib)
