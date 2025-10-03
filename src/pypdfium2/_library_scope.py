# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import atexit
import ctypes
import os
from typing import List, Optional
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i


def _create_font_path_array(font_paths: List[str]):
    """
    Create a null-terminated array of C strings from font paths for PDFium.
    Returns a pointer that can be used for FPDF_LIBRARY_CONFIG.m_pUserFontPaths.
    """
    if not font_paths:
        return None

    # Convert paths to bytes and add null terminator
    font_paths_bytes = [path.encode('utf-8') for path in font_paths]
    font_paths_bytes.append(None)  # Null terminator

    # Create array of c_char_p
    char_array = (ctypes.c_char_p * len(font_paths_bytes))(*font_paths_bytes)

    # Get the correct type from FPDF_LIBRARY_CONFIG structure
    font_path_type = pdfium_c.FPDF_LIBRARY_CONFIG._fields_[1][1]  # m_pUserFontPaths type

    # Cast to the expected type
    return ctypes.cast(char_array, font_path_type)


def init_lib(font_paths: Optional[List[str]] = None):
    """
    Initialize PDFium library with optional custom font paths.

    Args:
        font_paths: List of paths to font directories or font files that PDFium should use.
                   These will be used instead of or in addition to system fonts.
    """
    assert not pdfium_i.LIBRARY_AVAILABLE
    if pdfium_i.DEBUG_AUTOCLOSE:  # pragma: no cover
        # FIXME not shown on auto-init, because DEBUG_AUTOCLOSE can only be set on the caller side after pypdfium2 has been imported...
        print("Initialize PDFium", file=sys.stderr)

    # Handle font paths
    if font_paths:
        # Validate font paths exist
        valid_paths = []
        for path in font_paths:
            if os.path.exists(path):
                valid_paths.append(path)
            else:
                if pdfium_i.DEBUG_AUTOCLOSE:  # pragma: no cover
                    print(f"Warning: Font path does not exist: {path}", file=sys.stderr)

        font_paths_ptr = _create_font_path_array(valid_paths)
        if pdfium_i.DEBUG_AUTOCLOSE and valid_paths:  # pragma: no cover
            print(f"Loading {len(valid_paths)} custom font paths: {valid_paths}", file=sys.stderr)
    else:
        font_paths_ptr = None

    # PDFium init API may change in the future: https://crbug.com/pdfium/1446
    # NOTE Technically, FPDF_InitLibrary() would be sufficient for our purposes, but pdfium docs say "This will be deprecated in the future", so don't use it to be on the safe side. Also, avoid experimental config versions that might not be promoted to stable.
    config = pdfium_c.FPDF_LIBRARY_CONFIG(
        version = 2,
        m_pUserFontPaths = font_paths_ptr,
        m_pIsolate = None,
        m_v8EmbedderSlot = 0,
        # m_pPlatform = None,  # v3
        # m_RendererType = pdfium_c.FPDF_RENDERERTYPE_AGG,  # v4
    )
    pdfium_c.FPDF_InitLibraryWithConfig(config)
    pdfium_i.LIBRARY_AVAILABLE.value = True


def destroy_lib():  # pragma: no cover
    assert pdfium_i.LIBRARY_AVAILABLE
    if pdfium_i.DEBUG_AUTOCLOSE:
        pdfium_i._safe_debug("Destroy PDFium")
    pdfium_c.FPDF_DestroyLibrary()
    pdfium_i.LIBRARY_AVAILABLE.value = False


def initialize_with_fonts(font_paths: Optional[List[str]] = None):
    """
    Initialize pypdfium2 with custom font paths.

    This function should be called before any other pypdfium2 operations if you want to use
    custom local fonts instead of or in addition to system fonts.

    Args:
        font_paths: List of paths to font directories or specific font files (TTF, OTF, TTC).
                   PDFium will use these fonts when rendering PDFs.

    Example:
        import pypdfium2

        # Initialize with custom fonts
        pypdfium2.initialize_with_fonts([
            "/path/to/fonts/folder",
            "/path/to/specific/font.ttf"
        ])

        # Now use pypdfium2 normally
        pdf = pypdfium2.PdfDocument("document.pdf")
        ...
    """
    # If library is already initialized, we need to destroy and reinitialize
    if pdfium_i.LIBRARY_AVAILABLE:
        if pdfium_i.DEBUG_AUTOCLOSE:  # pragma: no cover
            pdfium_i._safe_debug("Re-initializing PDFium with custom fonts")
        # Note: This is not ideal but necessary for the API design
        destroy_lib()
        init_lib(font_paths)
    else:
        init_lib(font_paths)


# Load pdfium (default initialization without custom fonts)
init_lib()

# Register an exit handler that will free pdfium
# Trust in Python to call exit handlers only after all objects have been finalized
atexit.register(destroy_lib)
