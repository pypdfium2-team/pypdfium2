# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause 

import copy
import shutil
import tempfile
import pkg_resources
from os.path import join
import pypdfium2.version as pdfium_ver
from pl_setup import setup_base
import pl_setup.packaging_base as pkg_base
import pl_setup.update_pdfium as fpdf_up
import pl_setup.build_pdfium as fpdf_build


def _check_namespace(V_MAJOR, V_MINOR, V_PATCH, V_BETA, V_PYPDFIUM2, V_LIBPDFIUM, IS_SOURCEBUILD):
    
    for m in (V_MAJOR, V_MINOR, V_PATCH):
        assert isinstance(m, int)
    for m in (V_PYPDFIUM2, V_LIBPDFIUM):
        assert isinstance(m, str)
    
    assert isinstance(V_BETA, (type(None), int))
    assert isinstance(IS_SOURCEBUILD, bool)
    
    assert V_PYPDFIUM2.count(".") == 2
    if not IS_SOURCEBUILD:
        assert V_LIBPDFIUM.isnumeric()
    if V_BETA:
        assert "b" in V_PYPDFIUM2
        assert V_BETA >= 1
    
    assert V_MAJOR >= 2 and V_MINOR >= 0 and V_PATCH >= 0
    if V_LIBPDFIUM.isnumeric():
        assert int(V_LIBPDFIUM) > 5000


def test_current_version():
    _check_namespace(**pkg_base.VerNamespace)
    assert setup_base.SetupKws["version"] == pkg_base.VerNamespace["V_PYPDFIUM2"]

def test_installed_version():
    assert pkg_resources.get_distribution('pypdfium2').version == pdfium_ver.V_PYPDFIUM2


def _test_change(method, exp_items):
    
    exp_ns = copy.deepcopy(pkg_base.VerNamespace)
    for key, value in exp_items:
        exp_ns[key] = value
    
    method()
    
    assert exp_ns == pkg_base.VerNamespace
    new_ns = pkg_base.get_version_ns()
    exp_ns["V_PYPDFIUM2"] = new_ns["V_PYPDFIUM2"]
    assert exp_ns == new_ns


def test_setversion():
    
    tempdir = tempfile.TemporaryDirectory()
    orig_vfile = pkg_base.VersionFile
    tmp_vfile = join(tempdir.name, "tmp_versionfile.py")
    shutil.copy(orig_vfile, tmp_vfile)
    pkg_base.VersionFile = tmp_vfile
    
    exp_items = (
        ("IS_SOURCEBUILD", False),
        ("V_MAJOR", 2),
        ("V_MINOR", 0),
        ("V_PATCH", 0),
        ("V_BETA", None),
        ("V_LIBPDFIUM", "5005"),
    )
    for key, value in exp_items:
        pkg_base.set_version(key, value)
    
    _test_change(lambda: None, exp_items)
    _test_change(lambda: fpdf_up.handle_versions(5005), exp_items)
    
    _test_change(
        lambda: fpdf_up.handle_versions(5010),
        [
            ("V_MINOR", 1),
            ("V_LIBPDFIUM", "5010"),
        ]
    )
    _test_change(
        lambda: fpdf_build.update_version("abcdefg", "1234567", "5012"),
        [
            ("IS_SOURCEBUILD", True),
            ("V_LIBPDFIUM", "abcdefg"),
        ]
    )
    _test_change(
        lambda: fpdf_build.update_version("1234567", "1234567", "5012"),
        [
            ("V_LIBPDFIUM", "5012"),
        ]
    )
    _test_change(
        lambda: fpdf_up.handle_versions(5010),
        [
            ("IS_SOURCEBUILD", False),
            ("V_LIBPDFIUM", "5010"),
        ]
    )
    
    pkg_base.VersionFile = orig_vfile
    pkg_base.VerNamespace = pkg_base.get_version_ns()
    tempdir.cleanup()
