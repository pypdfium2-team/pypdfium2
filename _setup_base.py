#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
from os.path import (
    join,
    basename,
)
import shutil
import setuptools
from glob import glob
from typing import Callable
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
from _packaging import (
    Libnames,
    SourceTree,
    DataTree,
    ModuleDir,
    extract_version,
)

class PlatformDirs:
    Darwin64     = join(DataTree,'darwin-x64')
    DarwinArm64  = join(DataTree,'darwin-arm64')
    Linux64      = join(DataTree,'linux-x64')
    LinuxArm64   = join(DataTree,'linux-arm64')
    LinuxArm32   = join(DataTree,'linux-arm32')
    Windows64    = join(DataTree,'windows-x64')
    Windows86    = join(DataTree,'windows-x86')
    WindowsArm64 = join(DataTree,'windows-arm64')
    SourceBuild  = join(DataTree,'sourcebuild')


SetupKws = dict(
    version = extract_version('V_PYPDFIUM2'),
)


class BDistBase (_bdist_wheel):
    def finalize_options(self):
        _bdist_wheel.finalize_options(self)
        self.python_tag = 'py3'
        self.plat_name_supplied = True


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


def build(lib_setup: Callable, platform_dir):
    _clean()
    _copy_bindings(platform_dir)
    lib_setup()
    _clean()
