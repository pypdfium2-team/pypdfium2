# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import re
import pytest
# import sysconfig
# from pathlib import Path
# from wheel.bdist_wheel import bdist_wheel
from pypdfium2_setup import (
    # setup_base,
    packaging_base as pkg_base,
)
from pypdfium2_setup.packaging_base import (
    PlatNames,
    BinaryPlatforms,
    ReleaseNames,
)
from .conftest import ProjectDir, get_members


@pytest.fixture
def all_platnames():
    return list( get_members(PlatNames) )


# module

# NOTE migrated to pyproject.toml
# def test_entrypoint():
    
#     setup_cfg = configparser.ConfigParser()
#     setup_cfg.read( join(ProjectDir, "setup.cfg") )
#     console_scripts = setup_cfg["options.entry_points"]["console_scripts"]
    
#     entry_point = console_scripts.split("=")[-1].strip().split(":")
#     module_path = entry_point[0]
#     method_name = entry_point[1]
    
#     namespace = {}
#     exec("from %s import %s" % (module_path, method_name), namespace)
#     assert method_name in namespace
    
#     function = namespace[method_name]
#     assert callable(function)


# setup_base

ExpectedTags = (
    (PlatNames.linux_x64,        "manylinux_2_17_x86_64"),
    (PlatNames.linux_x86,        "manylinux_2_17_i686"),
    (PlatNames.linux_arm64,      "manylinux_2_17_aarch64"),
    (PlatNames.linux_arm32,      "manylinux_2_17_armv7l"),
    (PlatNames.linux_musl_x64,   "musllinux_1_1_x86_64"),
    (PlatNames.linux_musl_x86,   "musllinux_1_1_i686"),
    (PlatNames.linux_musl_arm64, "musllinux_1_1_aarch64"),
    (PlatNames.darwin_x64,       "macosx_10_13_x86_64"),
    (PlatNames.darwin_arm64,     "macosx_11_0_arm64"),
    (PlatNames.windows_x64,      "win_amd64"),
    (PlatNames.windows_arm64,    "win_arm64"),
    (PlatNames.windows_x86,      "win32"),
    # FIXME not sure how to test this
    # (PlatNames.sourcebuild,    ...),
)


def test_expected_tags(all_platnames):
    assert len(all_platnames) == len(ExpectedTags)+1
    for platform, tag in ExpectedTags:
        assert hasattr(PlatNames, platform)
        assert isinstance(tag, str)


def test_get_tag():
    for platform, tag in ExpectedTags:
        assert pkg_base.get_wheel_tag(platform) == tag

def test_unknown_tag():
    plat_dir = "win_amd74"
    with pytest.raises(ValueError, match=re.escape("Unknown platform name %s" % plat_dir)):
        pkg_base.get_wheel_tag(plat_dir)

# def test_get_bdist():
#     for platform, _ in ExpectedTags:
#         bdist_cls = setup_base.bdist_factory(platform)
#         assert issubclass(bdist_cls, bdist_wheel)


# packaging_base
# TODO update/extend

def test_libnames():
    for name in pkg_base.MainLibnames:
        assert "pdfium" in name

def test_PlatNames(all_platnames):
    # make sure variable names and values are identical
    for name in all_platnames:
        assert name == getattr(PlatNames, name)

def test_paths():
    # FIXME not much point doing this?
    assert pkg_base.ProjectDir == ProjectDir
    assert pkg_base.DataDir == ProjectDir / "data"
    assert pkg_base.SourcebuildDir == ProjectDir / "sourcebuild"
    assert pkg_base.ModuleDir_Helpers == ProjectDir / "src" / "pypdfium2"


# update_pdfium

def test_releasenames(all_platnames):
    assert len(ReleaseNames) == len(BinaryPlatforms) == len(all_platnames) - 1
    for key, value in ReleaseNames.items():
        assert key in BinaryPlatforms
        assert hasattr(PlatNames, key)
        system, cpu = value.replace("linux-musl", "musllinux").split("-", maxsplit=3)
        assert system in ("linux", "musllinux", "mac", "win")
        assert cpu in ("x64", "x86", "arm64", "arm")
