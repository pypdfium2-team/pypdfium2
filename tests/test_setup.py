# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import re
import pytest
import sysconfig
import configparser
from os.path import join
from pathlib import Path
from wheel.bdist_wheel import bdist_wheel
from pl_setup import (
    setup_base,
    packaging_base as pkg_base,
)
from pl_setup.packaging_base import (
    PlatformNames,
    BinaryPlatforms,
    ReleaseNames,
)
from .conftest import SourceTree, get_members


@pytest.fixture
def all_platnames():
    return list( get_members(PlatformNames) )


# module

def test_entrypoint():
    
    setup_cfg = configparser.ConfigParser()
    setup_cfg.read( join(SourceTree, "setup.cfg") )
    console_scripts = setup_cfg["options.entry_points"]["console_scripts"]
    
    entry_point = console_scripts.split("=")[-1].strip().split(":")
    module_path = entry_point[0]
    method_name = entry_point[1]
    
    namespace = {}
    exec("from %s import %s" % (module_path, method_name), namespace)
    assert method_name in namespace
    
    function = namespace[method_name]
    assert callable(function)


# setup_base

ExpectedTags = (
    (PlatformNames.linux_x64,      "manylinux_2_17_x86_64.manylinux2014_x86_64"),
    (PlatformNames.linux_x86,      "manylinux_2_17_i686.manylinux2014_i686"),
    (PlatformNames.linux_arm64,    "manylinux_2_17_aarch64.manylinux2014_aarch64"),
    (PlatformNames.linux_arm32,    "manylinux_2_17_armv7l.manylinux2014_armv7l"),
    (PlatformNames.linux_musl_x64, "musllinux_1_2_x86_64"),
    (PlatformNames.linux_musl_x86, "musllinux_1_2_i686"),
    (PlatformNames.darwin_x64,     "macosx_10_13_x86_64.macosx_11_0_x86_64.macosx_12_0_x86_64"),
    (PlatformNames.darwin_arm64,   "macosx_11_0_arm64.macosx_12_0_arm64"),
    (PlatformNames.windows_x64,    "win_amd64"),
    (PlatformNames.windows_arm64,  "win_arm64"),
    (PlatformNames.windows_x86,    "win32"),
    (PlatformNames.sourcebuild,    sysconfig.get_platform().replace('-','_').replace('.','_')),
)


def test_expected_tags(all_platnames):
    assert len(all_platnames) == len(ExpectedTags)
    for platform, tag in ExpectedTags:
        assert hasattr(PlatformNames, platform)
        assert isinstance(tag, str)


def test_get_tag():
    for platform, tag in ExpectedTags:
        assert pkg_base.get_wheel_tag(platform) == tag

def test_unknown_tag():
    plat_dir = "win_amd74"
    with pytest.raises(ValueError, match=re.escape("Unknown platform name %s" % plat_dir)):
        pkg_base.get_wheel_tag(plat_dir)

def test_get_bdist():
    for platform, _ in ExpectedTags:
        bdist_cls = setup_base.bdist_factory(platform)
        assert issubclass(bdist_cls, bdist_wheel)


# packaging_base
# TODO update/extend

def test_libnames():
    for name in pkg_base.MainLibnames:
        assert "pdfium" in name

def test_platformnames(all_platnames):
    # make sure variable names and values are identical
    for name in all_platnames:
        assert name == getattr(PlatformNames, name)

def test_paths():
    assert pkg_base.HomeDir == str( Path.home() )
    assert pkg_base.SourceTree == str(SourceTree)
    assert pkg_base.DataTree == str( Path(SourceTree) / "data" )
    assert pkg_base.SB_Dir == str( Path(SourceTree) / "sourcebuild" )
    assert pkg_base.ModuleDir == str( Path(SourceTree) / "src" / "pypdfium2" )
    assert pkg_base.VersionFile == str( Path(pkg_base.ModuleDir) / "version.py" )


# update_pdfium

def test_releasenames(all_platnames):
    assert len(ReleaseNames) == len(BinaryPlatforms) == len(all_platnames) - 1
    for key, value in ReleaseNames.items():
        assert key in BinaryPlatforms
        assert hasattr(PlatformNames, key)
        prefix, system, cpu = value.replace("linux-musl", "musllinux").split("-", maxsplit=3)
        assert prefix == "pdfium"
        assert system in ("linux", "musllinux", "mac", "win")
        assert cpu in ("x64", "x86", "arm64", "arm")
