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


class CleanerContext:
    
    def __init__(self):
        pass
    
    def __enter__(self):
        _clean()
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        _clean()


def _copy_bindings(platform_dir):
    
    # non-recursively collect all objects from the platform directory
    for src_path in glob(join(platform_dir,'*')):
        
        # copy platform-specific files into the sources, excluding possible directories
        if os.path.isfile(src_path):
            dest_path = join(ModuleDir, basename(src_path))
            shutil.copy(src_path, dest_path)


def _get_mac_tag(arch):
    return 'macosx_10_11_{}.macosx_11_0_{}'.format(arch, arch)

def _get_linux_tag(arch):
    return 'manylinux_2_17_{}.manylinux2014_{}'.format(arch, arch)


def _get_tags(plat_dir):
    if plat_dir is PlatformDirs.Darwin64:
        return _get_mac_tag('x86_64'), 'tmp_d64'
    elif plat_dir is PlatformDirs.DarwinArm64:
        return _get_mac_tag('arm64'), 'tmp_darm64'
    elif plat_dir is PlatformDirs.Linux64:
        return _get_linux_tag('x86_64'), 'tmp_l64'
    elif plat_dir is PlatformDirs.LinuxArm64:
        return _get_linux_tag('aarch64'), 'tmp_larm64'
    elif plat_dir is PlatformDirs.LinuxArm32:
        return _get_linux_tag('armv7l'), 'tmp_larm32'
    elif plat_dir is PlatformDirs.Windows64:
        return 'win_amd64', None
    elif plat_dir is PlatformDirs.Windows86:
        return 'win32', None
    elif plat_dir is PlatformDirs.WindowsArm64:
        return 'win_arm64', None
    elif plat_dir is PlatformDirs.SourceBuild:
        return sysconfig.get_platform(), None
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
    

SetupKws = dict(
    version = extract_version('V_PYPDFIUM2'),
)


def wheel_for(platform_dir):
    
    actual_tag, temp_tag = _get_tags(platform_dir)
    if temp_tag is not None:
        bdist_entry = _get_bdist(temp_tag)
    else:
        bdist_entry = _get_bdist(actual_tag)
    
    with CleanerContext():
        _copy_bindings(platform_dir)
        setuptools.setup(
            cmdclass = {'bdist_wheel': bdist_entry},
            package_data = {'': Libnames},
            **SetupKws,
        )
    
    if temp_tag is not None:
        _rename_wheel(temp_tag, actual_tag)
