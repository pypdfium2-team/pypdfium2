#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
from os.path import (
    dirname,
    realpath,
    join,
    basename,
    exists,
)
from glob import glob
import shutil
import setuptools
from typing import Callable
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel


SourceTree = dirname(realpath(__file__))
TargetDir  = join(SourceTree,'src','pypdfium2')
DataTree   = join(SourceTree,'data')

Darwin64     = join(DataTree,'darwin-x64')
DarwinArm64  = join(DataTree,'darwin-arm64')
Linux64      = join(DataTree,'linux-x64')
LinuxArm64   = join(DataTree,'linux-arm64')
LinuxArm32   = join(DataTree,'linux-arm32')
Windows64    = join(DataTree,'windows-x64')
Windows86    = join(DataTree,'windows-x86')
SourceBuild  = join(DataTree,'sourcebuild')


class BDistBase (_bdist_wheel):
    def finalize_options(self):
        _bdist_wheel.finalize_options(self)
        self.python_tag = 'py3'
        self.plat_name_supplied = True


def _clean():
    
    build_cache    = join(SourceTree,'build')
    bindings_file  = join(TargetDir,'_pypdfium.py')
    
    binary_linux   = join(TargetDir,'pdfium')
    binary_windows = join(TargetDir,'pdfium.dll')
    binary_darwin  = join(TargetDir,'pdfium.dylib')
    
    files = [bindings_file, binary_linux, binary_windows, binary_darwin]
    
    if exists(build_cache):
        shutil.rmtree(build_cache)
    
    for file in files:
        if exists(file):
            os.remove(file)


def _copy_bindings(platform_dir):
    platform_files = glob(join(platform_dir,'*'))
    for src in platform_files:
        if os.path.isfile(src):
            dest = join(TargetDir, basename(src))
            shutil.copy(src, dest)


def build(lib_setup: Callable, platform_dir):
    _clean()
    _copy_bindings(platform_dir)
    lib_setup()
    _clean()
