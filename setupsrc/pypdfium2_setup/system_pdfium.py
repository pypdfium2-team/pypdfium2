# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# NOTE: this code is provided on a best effort basis and is largely untested, because the author's system did not provide pdfium as of this writing

import sys
import itertools
from pathlib import Path
from ctypes.util import find_library

sys.path.insert(0, str(Path(__file__).parents[1]))
from pypdfium2_setup.base import *


def _get_existing(candidates):
    return next((p for p in candidates if p.exists()), None)


def _find_pdfium_lib():
    
    # See if a pdfium shared library is in the default system search path
    pdfium_lib = find_library("pdfium")
    
    # Look for pdfium bundled with libreoffice. (Assuming the unknown host has a unix-like file system)
    # Not sure how complete or incomplete libreoffice's pdfium builds are; this is just a chance.
    if not pdfium_lib and not sys.platform.startswith(("win", "darwin")):
        lo_paths_iter = itertools.product(("/usr/lib", "/usr/local/lib"), ("", "64"))
        libname = libname_for_system(Host.system, name="pdfiumlo")
        candidates = (Path(prefix+bitness)/"libreoffice"/"program"/libname for prefix, bitness in lo_paths_iter)
        pdfium_lib = _get_existing(candidates)
    
    return pdfium_lib


def _find_pdfium_headers():
    
    headers_path = os.getenv("PDFIUM_HEADERS")
    
    if headers_path:
        headers_path = Path(headers_path)
    elif not sys.platform.startswith(("win", "darwin")):
        include_dirs = (Path("/usr/include"), Path("/usr/local/include"))
        candidates = (prefix/"pdfium" for prefix in include_dirs)
        headers_path = _get_existing(candidates)
        if not headers_path:
            candidates = (prefix/"fpdf_edit.h" for prefix in include_dirs)
            sample_header = _get_existing(candidates)
            if sample_header:
                headers_path = sample_header.parent
    
    return headers_path


def find_pdfium():
    pdfium_lib = _find_pdfium_lib()
    pdfium_headers = _find_pdfium_headers()
    if pdfium_lib:
        log(f"Found pdfium shared library at {pdfium_lib}")
        if pdfium_headers:
            log(f"Found pdfium headers at {pdfium_headers}")
        else:
            log(f"pdfium headers not found - will use reference bindings. Warning: This is ABI-unsafe. Set $PDFIUM_HEDERS and re-run if you know the headers.")
    else:
        log("pdfium not found")
    return pdfium_lib, pdfium_headers
