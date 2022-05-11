# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import shutil
import tempfile
from os.path import join
from pl_setup import update_pdfium as fpdf_up
from pl_setup.packaging_base import (
    PlatformNames,
    VersionFile,
    VerNamespace,
    _get_ver_namespace,
)
from ..conftest import pl_names


def test_consts():
    assert fpdf_up.ReleaseRepo == "https://github.com/bblanchon/pdfium-binaries"
    assert fpdf_up.ReleaseURL == "https://github.com/bblanchon/pdfium-binaries/releases/download/chromium%2F"
    assert fpdf_up.ReleaseExtension == "tgz"


def test_releasenames():
    assert len(fpdf_up.ReleaseNames) == len(pl_names) - 1
    for key, value in fpdf_up.ReleaseNames.items():
        assert hasattr(PlatformNames, key)
        prefix, system, cpu = value.replace("linux-musl", "musllinux").split("-", maxsplit=3)
        assert prefix == "pdfium"
        assert system in ("linux", "musllinux", "mac", "win")
        assert cpu in ("x64", "x86", "arm64", "arm")


def test_setversion():
    
    tempdir = tempfile.TemporaryDirectory()
    tmp_versionfile = join(tempdir.name, "tmp_versionfile.py")
    shutil.copy(VersionFile, tmp_versionfile)
    
    target_version = VerNamespace["V_LIBPDFIUM"] + 10
    fpdf_up.handle_versions(tmp_versionfile, target_version)
    new_vernsp = _get_ver_namespace(tmp_versionfile)
    
    assert new_vernsp["V_LIBPDFIUM"] == target_version
    assert new_vernsp["V_MINOR"] == VerNamespace["V_MINOR"] + 1
    
    tempdir.cleanup()


def test_getversion():
    latest = fpdf_up.get_latest_version()
    assert latest > 5000
    assert latest >= VerNamespace["V_LIBPDFIUM"]
