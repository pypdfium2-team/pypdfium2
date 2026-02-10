# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0 OR Apache-2.0 OR BSD-3-Clause

# minimal test confirming we can call the library

import sys
import atexit
import pypdfium2_raw as pdfium

atexit.register(pdfium.FPDF_DestroyLibrary)

# see pypdfium2::_library_scope.py
init_config = pdfium.FPDF_LIBRARY_CONFIG(
    version = 2,
    m_pUserFontPaths = None,
    m_pIsolate = None,
    m_v8EmbedderSlot = 0,
)
pdfium.FPDF_InitLibraryWithConfig(init_config)

doc = pdfium.FPDF_CreateNewDocument()
page = pdfium.FPDFPage_New(doc, 0, 595, 842)
pdfium.FPDF_ClosePage(page)
pdfium.FPDF_CloseDocument(doc)

if sys.platform.startswith("win32"):
    assert hasattr(pdfium, "FPDF_RenderPage"), "Windows-only API is missing"
