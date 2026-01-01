# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# NOTE: This code is provided on a best effort basis. It is relatively hard for us to test.

import re
import sys
import shutil
import itertools
from pathlib import Path
from ctypes.util import find_library
from urllib.request import urlopen

from base import *  # local


def _get_existing(candidates, cb=Path.exists):
    return next((p for p in candidates if cb(p)), None)

def _removeprefix(string, prefix):
    if string.startswith(prefix):
        string = string[len(prefix):]
    return string


def _find_pdfium_headers():
    
    headers_path = os.getenv("PDFIUM_HEADERS")
    if headers_path:
        return Path(headers_path)
    
    if not sys.platform.startswith(("win", "darwin")):
        include_dirs = (Host.usr/"include", Host.usr/"local"/"include")
        candidates = (path/"pdfium" for path in include_dirs)
        headers_path = _get_existing(candidates, cb=Path.is_dir)
        if headers_path:
            return headers_path
        
        candidates = (path/"fpdf_edit.h" for path in include_dirs)
        sample_header = _get_existing(candidates, cb=Path.is_file)
        if sample_header:
            return sample_header.parent
    
    return None

def _parse_version(version):
    if "." in version:
        version = PdfiumVer.scheme(*[int(v) for v in version.split(".")])
    else:
        version = PdfiumVer.to_full(int(version))
    assert version.build > 1000, "unexpected versioning scheme, or grossly outdated"
    return version

def _get_sys_pdfium_ver(pdfium_lib):
    
    log("Trying to determine system pdfium version ...")
    
    libname_parts = Path(pdfium_lib).name.split(".", maxsplit=2)
    if len(libname_parts) == 3:
        return _parse_version(libname_parts[2])
    
    if shutil.which("pkg-config"):
        proc = run_cmd(["pkg-config", "--modversion", "libpdfium"], cwd=None, check=False)
        if proc.returncode == 0:
            version = proc.stdout.decode().strip()
            return _parse_version(version)
    
    log("Unable to identify version, will set NaN placeholders.")
    return PdfiumVerUnknown


def _yield_lo_candidates(system):
    lo_paths_iter = itertools.product(
        (Host.usr/"lib", Host.usr/"local"/"lib"), ("", "64")
    )
    libname = libname_for_system(system, name="pdfiumlo")
    yield from (
        Path(str(path)+bitness)/"libreoffice"/"program"/libname
        for path, bitness in lo_paths_iter
    )

def _find_lo_pdfium():
    # Look for pdfium bundled with libreoffice, assuming a unix-like filesystem hierarchy.
    pdfium_lib = None
    if not sys.platform.startswith(("win", "darwin")):
        candidates = _yield_lo_candidates(Host.system)
        pdfium_lib = _get_existing(candidates)
    return pdfium_lib

def _get_lo_pdfium_ver():
    log("Trying to determine libreoffice pdfium version ...")
    
    output = run_cmd(["libreoffice", "--version"], cwd=None, capture=True)
    # alternatively, we could do e.g.: re.search(r"([\d\.]+)", output)
    output = _removeprefix(output.lower(), "libreoffice").lstrip()
    lo_version = output.split(" ")[0]
    log(f"Libreoffice version: {lo_version!r}")
    
    deps_url = f"https://raw.githubusercontent.com/LibreOffice/core/refs/tags/libreoffice-{lo_version}/download.lst"
    deps_content = urlopen(deps_url).read().decode("utf-8")
    match = re.search(r"pdfium-(\d+)\.tar\.bz2", deps_content, flags=re.MULTILINE)
    short_ver = int(match.group(1))
    log(f"Libreoffice pdfium version: {short_ver}")
    
    return PdfiumVer.to_full(short_ver)


class PdfiumNotFoundError (RuntimeError):
    pass


def _yield_pdfium_candidates():
    # give the caller an opportunity to set the pdfium path
    yield os.getenv("PDFIUM_BINARY"), "caller"
    # see if a pdfium shared library is in the default system search path
    yield find_library("pdfium"), "ctypes"
    # see if libreoffice provides pdfium
    yield _find_lo_pdfium(), "libreoffice"

def _get_pdfium():
    candidates = _yield_pdfium_candidates()
    for pdfium_lib, finder in candidates:
        if pdfium_lib:
            return pdfium_lib, finder
    # abort if none of this worked
    raise PdfiumNotFoundError("Could not find system pdfium.")


def main(given_fullver=None, flags=(), target_dir=DataDir/ExtPlats.system):
    
    log("Looking for system pdfium ...")
    pdfium_lib, finder = _get_pdfium()
    
    log(f"Found pdfium shared library at {pdfium_lib} ({finder})")
    target_path = target_dir/BindingsFN
    kwargs = dict(univ_paths=(pdfium_lib,), guard_symbols=True, flags=flags)
    
    if finder == "libreoffice":
        full_ver = given_fullver or _get_lo_pdfium_ver()
        # assuming libreoffice does not change the original pdfium ABI
        build_pdfium_bindings(full_ver.build, **kwargs)
        bindings_path = BindingsFile
    else:
        pdfium_headers = _find_pdfium_headers()
        full_ver = given_fullver or _get_sys_pdfium_ver(pdfium_lib)
        if pdfium_headers:
            log(f"Found pdfium headers at {pdfium_headers}")
            run_ctypesgen(target_path, pdfium_headers, version=full_ver.build, **kwargs)
            bindings_path = target_path
        elif full_ver is not PdfiumVerUnknown:
            log(f"Could not find headers, but know the version: {full_ver}")
            build_pdfium_bindings(full_ver.build, **kwargs)
            bindings_path = BindingsFile
        else:
            log(f"Warning: Neither pdfium headers nor version found - will use reference bindings. This is ABI-unsafe! Set $PDFIUM_HEADERS to the directory in question, or pass the version via $PDFIUM_PLATFORM=system-search:$VERSION.")
            bindings_path = RefBindingsFile
    
    write_pdfium_info(target_dir, full_ver, origin=f"system-{finder}", flags=flags)
    if bindings_path != target_path:
        shutil.copyfile(bindings_path, target_path)
    if full_ver.build < PDFIUM_MIN_REQ:
        log(f"Warning: pdfium version {full_ver.build} does not conform with minimum requirement {PDFIUM_MIN_REQ}. Some APIs may not work. Run pypdfium2's test suite for details.")
    
    return full_ver


if __name__ == "__main__":
    # print(_get_lo_pdfium_ver())
    # print(_find_pdfium_headers())
    # print(_get_sys_pdfium_ver("libpdfium.so.140.0.7295.0"))
    print(main())
