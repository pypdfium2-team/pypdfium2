#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
from os.path import (
    join,
    basename,
)
import shutil
import sysconfig
import setuptools
from glob import glob
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

from platform_setup.packaging_base import (
    Libnames,
    SourceTree,
    ModuleDir,
    PlatformDirs,
    extract_version,
)


def _get_bdist(whl_tag):
    
    class bdist (_bdist_wheel):
        def __init__(self, *args, **kwargs):
            _bdist_wheel.__init__(self, *args, **kwargs)
            self.python_tag = 'py3'
            self.plat_name = whl_tag
            self.plat_name_supplied = True
    
    return bdist


def _clean():
    
    build_cache    = join(SourceTree,'build')
    bindings_file  = join(ModuleDir,'_pypdfium.py')
    
    libpaths = []
    for name in Libnames:
        libpaths.append( join(ModuleDir, name) )
    
    files = [bindings_file, *libpaths]
    
    if os.path.exists(build_cache):
        shutil.rmtree(build_cache)
    
    for file in files:
        if os.path.exists(file):
            os.remove(file)


def _copy_bindings(platform_dir):
    
    # non-recursively collect all objects from the platform directory
    for src_path in glob(join(platform_dir,'*')):
        
        # copy platform-specific files into the sources, excluding possible directories
        if os.path.isfile(src_path):
            dest_path = join(ModuleDir, basename(src_path))
            shutil.copy(src_path, dest_path)


def _get_tag(plat_dir):
    if plat_dir is PlatformDirs.Darwin64:
        return 'macosx_10_11_x86_64'
    elif plat_dir is PlatformDirs.DarwinArm64:
        return 'macosx_11_0_arm64'
    elif plat_dir is PlatformDirs.Linux64:
        return 'manylinux_2_17_x86_64'
    elif plat_dir is PlatformDirs.LinuxArm64:
        return 'manylinux_2_17_aarch64'
    elif plat_dir is PlatformDirs.LinuxArm32:
        return 'manylinux_2_17_armv7l'
    elif plat_dir is PlatformDirs.Windows64:
        return 'win_amd64'
    elif plat_dir is PlatformDirs.Windows86:
        return 'win32'
    elif plat_dir is PlatformDirs.WindowsArm64:
        return 'win_arm64'
    elif plat_dir is PlatformDirs.SourceBuild:
        return sysconfig.get_platform()
    else:
        raise ValueError( "Unknown platform directory {}".format(plat_dir) )

   
SetupKws = dict(
    version = extract_version('V_PYPDFIUM2'),
)

def wheel_for(platform_dir):
    _clean()
    _copy_bindings(platform_dir)
    tag = _get_tag(platform_dir)
    setuptools.setup(
        cmdclass = {'bdist_wheel': _get_bdist(tag)},
        package_data = {'': Libnames},
        **SetupKws,
    )
    _clean()
