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
        def finalize_options(self, *args, **kwargs):
            _bdist_wheel.finalize_options(self, *args, **kwargs)
            self.python_tag = 'py3'
            self.plat_name = whl_tag
            self.plat_name_supplied = True
    
    return bdist


def _clean():
    
    build_cache = join(SourceTree,'build')
    bindings_file = join(ModuleDir,'_pypdfium.py')
    
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


SetupKws = dict(
    version = extract_version('V_PYPDFIUM2'),
)


def _get_tags(plat_dir):
    if plat_dir is PlatformDirs.Darwin64:
        return 'tmp_d64', 'macosx_10_11_x86_64.macosx_11_0_x86_64'
    elif plat_dir is PlatformDirs.DarwinArm64:
        return 'tmp_darm64', 'macosx_10_11_arm64.macosx_11_0_arm64'
    elif plat_dir is PlatformDirs.Linux64:
        return 'tmp_l64', 'manylinux_2_17_x86_64.manylinux2014_x86_64'
    elif plat_dir is PlatformDirs.LinuxArm64:
        return 'tmp_larm64', 'manylinux_2_17_aarch64.manylinux2014_aarch64'
    elif plat_dir is PlatformDirs.LinuxArm32:
        return 'tmp_larm32', 'manylinux_2_17_armv7l.manylinux2014_armv7l'
    elif plat_dir is PlatformDirs.Windows64:
        return None, 'win_amd64'
    elif plat_dir is PlatformDirs.Windows86:
        return None, 'win32'
    elif plat_dir is PlatformDirs.WindowsArm64:
        return None, 'win_arm64'
    elif plat_dir is PlatformDirs.SourceBuild:
        return None, sysconfig.get_platform()
    else:
        raise ValueError( "Unknown platform directory {}".format(plat_dir) )


def _rename_wheel(temp_tag, actual_tag):
    
    dist_dir = join(SourceTree, 'dist')
        
    found_names = [f for f in os.listdir(dist_dir) if temp_tag in f]
    assert len(found_names) == 1
    
    src_path = join(dist_dir, found_names[0])
    assert os.path.isfile(src_path)
    dest_path = src_path.replace(temp_tag, actual_tag, 1)
    
    print( "Renaming wheel: {} -> {}".format(src_path, dest_path) )
    os.rename(src_path, dest_path)
    


def wheel_for(platform_dir):
    
    temp_tag, actual_tag = _get_tags(platform_dir)
    if temp_tag is not None:
        bdist_entry = _get_bdist(temp_tag)
    else:
        bdist_entry = _get_bdist(actual_tag)
    
    _clean()
    _copy_bindings(platform_dir)
    
    setuptools.setup(
        cmdclass = {'bdist_wheel': bdist_entry},
        package_data = {'': Libnames},
        **SetupKws,
    )
    
    _clean()
    if temp_tag is not None:
        _rename_wheel(temp_tag, actual_tag)
