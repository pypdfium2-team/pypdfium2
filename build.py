#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import os
import shutil
import sys
from glob import glob
from os.path import basename, dirname, exists, join, realpath
from typing import Callable

import setuptools
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel


SourceTree = dirname(realpath(__file__))
TargetDir = join(SourceTree, "src", "pypdfium2")
DataTree = join(SourceTree, "data")

Darwin64 = join(DataTree, "darwin-x64")
DarwinArm64 = join(DataTree, "darwin-arm64")
Linux64 = join(DataTree, "linux-x64")
LinuxArm64 = join(DataTree, "linux-arm64")
LinuxArm32 = join(DataTree, "linux-arm32")
Windows64 = join(DataTree, "windows-x64")
Windows86 = join(DataTree, "windows-x86")


class BDistBase(_bdist_wheel):
    def finalize_options(self):
        _bdist_wheel.finalize_options(self)
        self.python_tag = "py3"
        self.plat_name_supplied = True


def _clean():
    build_cache = join(SourceTree, "build")
    bindings_file = join(TargetDir, "_pypdfium.py")

    binary_linux = join(TargetDir, "pdfium")
    binary_windows = join(TargetDir, "pdfium.dll")
    binary_darwin = join(TargetDir, "pdfium.dylib")

    files = [bindings_file, binary_linux, binary_windows, binary_darwin]

    if exists(build_cache):
        shutil.rmtree(build_cache)

    for file in files:
        if exists(file):
            os.remove(file)


def _copy_bindings(platform_dir):
    for file in glob(join(platform_dir, "*")):
        file_basename = basename(file)
        shutil.copy(file, join(TargetDir, file_basename))


def build(lib_setup: Callable, platform_dir):
    _clean()
    _copy_bindings(platform_dir)
    lib_setup()
    _clean()


if __name__ == "__main__":
    sys.argv.append("bdist")

    for platform in (
        ("manylinux_2_17_x86_64", Linux64),
        ("macosx_10_10_x86_64", Darwin64),
        # see https://discuss.python.org/t/wheel-platform-tag-for-windows/9025/4
        ("win_amd64", Windows64),
        ("win32", Windows86),
        ("macosx_11_0_arm64", DarwinArm64),
        ("manylinux_2_17_armv7l", LinuxArm32),
        ("manylinux_2_17_aarch64", LinuxArm64),
    ):

        class bdist(BDistBase):
            def finalize_options(self):
                BDistBase.finalize_options(self)
                self.plat_name = platform

        def lib_setup():
            setuptools.setup(
                cmdclass={"bdist_wheel": bdist},
                package_data={"": ["pdfium"]},
            )

        build(lib_setup, Linux64)
