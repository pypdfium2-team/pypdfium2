# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import shutil
import tempfile
import subprocess
import functools
import urllib.request
from pathlib import Path
from os.path import join, isfile
from concurrent.futures import ThreadPoolExecutor
import pytest
from ..conftest import SourceTree, pl_names
from pl_setup import packaging_base as pkg_base


def test_libnames():
    for name in pkg_base.Libnames:
        assert "pdfium" in name

def test_platformnames():
    for member in pl_names:
        assert member == getattr(pkg_base.PlatformNames, member)

def test_version_namespace():
    vars = ("V_MAJOR", "V_MINOR", "V_PATCH", "V_BETA", "V_PYPDFIUM2", "V_LIBPDFIUM")
    for var in vars:
        assert var in pkg_base.VerNamespace
        assert isinstance(pkg_base.VerNamespace[var], (str, int, type(None)))

def test_paths():
    assert pkg_base.HomeDir == str( Path.home() )
    assert pkg_base.SourceTree == SourceTree
    assert pkg_base.DataTree == str( Path(SourceTree) / "data" )
    assert pkg_base.SB_Dir == str( Path(SourceTree) / "sourcebuild" )
    assert pkg_base.ModuleDir == str( Path(SourceTree) / "src" / "pypdfium2" )
    assert pkg_base.VersionFile == str( Path(pkg_base.ModuleDir) / "_version.py" )


Git = shutil.which("git")

@pytest.mark.skipif(not Git, reason="git not installed")
def test_run_cmd():
    comp_process = pkg_base.run_cmd([Git, "--version"], cwd=None)
    assert isinstance(comp_process, subprocess.CompletedProcess)
    message = pkg_base.run_cmd([Git, "status"], cwd=SourceTree, capture=True)
    assert isinstance(message, str)


def _get_header(url_prefix, include_dir, filename):
    return urllib.request.urlretrieve(url_prefix+filename, join(include_dir.name, filename))

@pytest.mark.skipif(not shutil.which("ctypesgen"), reason="ctypesgen not installed")
def test_call_ctypesgen():
    
    plat_dir = tempfile.TemporaryDirectory()
    include_dir = tempfile.TemporaryDirectory()
    
    header_files = ("fpdfview.h", "fpdf_searchex.h", "fpdf_catalog.h")
    url_prefix = "https://raw.githubusercontent.com/chromium/pdfium/main/public/"
    with ThreadPoolExecutor( len(header_files) ) as pool:
        for rc in pool.map(functools.partial(_get_header, url_prefix, include_dir), header_files):
            pass
    
    pkg_base.call_ctypesgen(plat_dir.name, include_dir.name)
    bindings_file = join(plat_dir.name, "_pypdfium.py")
    assert isfile(bindings_file)
    
    with open(bindings_file, "r") as fh:
        text = fh.read()
        assert "FPDFCatalog_IsTagged" in text
        assert "FPDFText_GetCharIndexFromTextIndex" in text
    
    plat_dir.cleanup()
    include_dir.cleanup()
