# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sysconfig
from pl_setup import setup_base
from pl_setup.packaging_base import PlatformNames


def test_get_tag():
    exp_tags = (
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
    
    for platform, tag in exp_tags:
        assert setup_base._get_tag(platform) == tag
    
    n_platforms = 0
    for member in dir(PlatformNames):
        if member.startswith('_'):
            continue
        n_platforms += 1
    
    assert n_platforms == len(exp_tags)
    
