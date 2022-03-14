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
    DataTree,
    SourceTree,
    ModuleDir,
    PlatformNames,
    extract_version,
)


def _clean():
    
    build_cache = join(SourceTree,'build')
    if os.path.exists(build_cache):
        shutil.rmtree(build_cache)
    
    delete_files = [join(ModuleDir, n) for n in (*Libnames, '_pypdfium.py')]
    
    for file in delete_files:
        if os.path.exists(file):
            os.remove(file)


def _copy_bindings(pl_name):
    
    # non-recursively collect all objects from the platform directory
    for src_path in glob(join(DataTree, pl_name, '*')):
        
        # copy platform-specific files into the sources, excluding possible directories
        if os.path.isfile(src_path):
            dest_path = join(ModuleDir, basename(src_path))
            shutil.copy(src_path, dest_path)


def _get_linux_tag(arch):
    return 'manylinux_2_17_{}.manylinux2014_{}'.format(arch, arch)


def _get_mac_tag(arch, *versions):
    
    assert len(versions) > 0
    
    template = 'macosx_{}_{}'
    
    tag = ''
    sep = ''
    for v in versions:
        tag += sep + template.format(v, arch)
        sep = '.'
    
    return tag


def _get_tag(pl_name):
    if pl_name == PlatformNames.darwin_x64:
        return _get_mac_tag('x86_64', '10_11', '11_0', '12_0')
    elif pl_name == PlatformNames.darwin_arm64:
        return _get_mac_tag('arm64', '11_0', '12_0')
    elif pl_name == PlatformNames.linux_x64:
        return _get_linux_tag('x86_64')
    elif pl_name == PlatformNames.linux_x86:
        return _get_linux_tag('i686')
    elif pl_name == PlatformNames.linux_arm64:
        return _get_linux_tag('aarch64')
    elif pl_name == PlatformNames.linux_arm32:
        return _get_linux_tag('armv7l')
    elif pl_name == PlatformNames.windows_x64:
        return 'win_amd64'
    elif pl_name == PlatformNames.windows_arm64:
        return 'win_arm64'
    elif pl_name == PlatformNames.windows_x86:
        return 'win32'
    elif pl_name == PlatformNames.sourcebuild:
        tag = sysconfig.get_platform()
        for char in ('-', '.'):
            tag = tag.replace(char, '_')
        return tag
    else:
        raise ValueError( "Unknown platform directory {}".format(pl_name) )


def _get_bdist(pl_name):
    
    class bdist (_bdist_wheel):
        
        def finalize_options(self, *args, **kws):
            _bdist_wheel.finalize_options(self, *args, **kws)
            self.plat_name_supplied = True
        
        def get_tag(self, *args, **kws):
            return 'py3', 'none', _get_tag(pl_name)
    
    return bdist


SetupKws = dict(
    version = extract_version('V_PYPDFIUM2'),
)


def mkwheel(pl_name):
    
    _clean()
    _copy_bindings(pl_name)
    
    setuptools.setup(
        package_data = {'': Libnames},
        cmdclass = {'bdist_wheel': _get_bdist(pl_name)},
        **SetupKws,
    )
    
    _clean()
