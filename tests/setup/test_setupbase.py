# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sysconfig
from wheel.bdist_wheel import bdist_wheel
import pytest
from pl_setup import setup_base
from pl_setup.packaging_base import PlatformNames, VerNamespace
from ..conftest import pl_names


ExpectedTags = (
    (PlatformNames.darwin_x64,    "macosx_10_11_x86_64.macosx_11_0_x86_64.macosx_12_0_x86_64"),
    (PlatformNames.darwin_arm64,  "macosx_11_0_arm64.macosx_12_0_arm64"),
    (PlatformNames.linux_x64,     "manylinux_2_17_x86_64.manylinux2014_x86_64"),
    (PlatformNames.linux_x86,     "manylinux_2_17_i686.manylinux2014_i686"),
    (PlatformNames.linux_arm64,   "manylinux_2_17_aarch64.manylinux2014_aarch64"),
    (PlatformNames.linux_arm32,   "manylinux_2_17_armv7l.manylinux2014_armv7l"),
    (PlatformNames.musllinux_x64, "musllinux_1_2_x86_64"),
    (PlatformNames.musllinux_x86, "musllinux_1_2_i686"),
    (PlatformNames.windows_x64,   "win_amd64"),
    (PlatformNames.windows_arm64, "win_arm64"),
    (PlatformNames.windows_x86,   "win32"),
    (PlatformNames.sourcebuild,   sysconfig.get_platform().replace('-','_').replace('.','_')),
)


def test_expected_tags():
    assert len(pl_names) == len(ExpectedTags)
    for platform, tag in ExpectedTags:
        assert hasattr(PlatformNames, platform)
        assert isinstance(tag, str)


def test_get_tag():
    for platform, tag in ExpectedTags:
        assert setup_base._get_tag(platform) == tag

def test_unknown_tag():
    plat_dir = "win_amd74"
    with pytest.raises(ValueError, match="Unknown platform directory %s" % plat_dir):
        setup_base._get_tag(plat_dir)

def test_get_bdist():
    for platform, tag in ExpectedTags:
        bdist_cls = setup_base._get_bdist(platform)
        assert issubclass(bdist_cls, bdist_wheel)

def test_setupkws():
    assert "version" in setup_base.SetupKws
    assert setup_base.SetupKws["version"] == VerNamespace["V_PYPDFIUM2"]
