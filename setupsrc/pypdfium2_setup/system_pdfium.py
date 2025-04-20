# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# NOTE: this code is provided on a best effort basis and largely untested, because the author's system did not provide pdfium as of this writing

import re
import sys
import itertools
from pathlib import Path
from ctypes.util import find_library
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).parents[1]))
from pypdfium2_setup.base import *


def _get_existing(candidates, cb=Path.exists):
    return next((p for p in candidates if cb(p)), None)


def _find_pdfium_lib():
    
    # See if a pdfium shared library is in the default system search path
    pdfium_lib = find_library("pdfium")
    from_lo = False
    
    # Look for pdfium bundled with libreoffice. (Assuming the unknown host has a unix-like file system)
    # Not sure how complete or incomplete libreoffice's pdfium builds are; this is just a chance
    if not pdfium_lib and not sys.platform.startswith(("win", "darwin")):
        lo_paths_iter = itertools.product(("/usr/lib", "/usr/local/lib"), ("", "64"))
        libname = libname_for_system(Host.system, name="pdfiumlo")
        candidates = (Path(prefix+bitness)/"libreoffice"/"program"/libname for prefix, bitness in lo_paths_iter)
        pdfium_lib = _get_existing(candidates)
        if pdfium_lib:
            from_lo = True
    
    return pdfium_lib, from_lo


def _find_pdfium_headers():
    
    headers_path = os.getenv("PDFIUM_HEADERS")
    
    if headers_path:
        headers_path = Path(headers_path)
    elif not sys.platform.startswith(("win", "darwin")):
        include_dirs = (Path("/usr/include"), Path("/usr/local/include"))
        candidates = (prefix/"pdfium" for prefix in include_dirs)
        headers_path = _get_existing(candidates, cb=Path.is_dir)
        if not headers_path:
            candidates = (prefix/"fpdf_edit.h" for prefix in include_dirs)
            sample_header = _get_existing(candidates, cb=Path.is_file)
            if sample_header:
                headers_path = sample_header.parent
    
    return headers_path


def _removeprefix(string, prefix):
    if string.startswith(prefix):
        string = string[len(prefix):]
    return string


def _get_libreoffice_pdfium_ver():
    log("Trying to determine libreoffice pdfium version ...")
    
    output = run_cmd(["libreoffice", "--version"], cwd=None, capture=True)
    # alternatively, we could do e.g.: re.search(r"([\d\.]+)", output)
    output = _removeprefix(output.lower(), "libreoffice").lstrip()
    lo_version = output.split(" ")[0]
    log(f"Libreoffice version: {lo_version!r}")
    
    deps_url = f"https://raw.githubusercontent.com/LibreOffice/core/refs/tags/libreoffice-{lo_version}/download.lst"
    deps_content = urlopen(deps_url).read().decode("utf-8")
    match = re.search(r"pdfium-(\d+)\.tar\.bz2", deps_content, flags=re.MULTILINE)
    pdfium_ver = int(match.group(1))
    log(f"Libreoffice pdfium version: {pdfium_ver}")
    
    return pdfium_ver
    

def find_pdfium():
    pdfium_lib, from_lo = _find_pdfium_lib()
    pdfium_headers = None
    if pdfium_lib:
        log(f"Found pdfium shared library at {pdfium_lib} (from_lo={from_lo})")
        if not from_lo:
            pdfium_headers = _find_pdfium_headers()
            if pdfium_headers:
                log(f"Found pdfium headers at {pdfium_headers}")
            else:
                log(f"pdfium headers not found - will use reference bindings. Warning: This is ABI-unsafe. Install the headers and/or set $PDFIUM_HEADERS to the directory in question.")
    else:
        log("pdfium not found")
    return pdfium_lib, from_lo, pdfium_headers


if __name__ == "__main__":
    print(find_pdfium())
    print(_get_libreoffice_pdfium_ver())
