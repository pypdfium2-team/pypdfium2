#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sysconfig
import setuptools
import build_pdfium

from _setup_base import (
    PlatformDirs,
    BDistBase,
    SetupKws,
    build,
)


class bdist (BDistBase):
    def finalize_options(self):
        BDistBase.finalize_options(self)
        self.plat_name = sysconfig.get_platform()


def lib_setup(libname):
    setuptools.setup(
        cmdclass = {'bdist_wheel': bdist},
        package_data = {'': [libname]},
        **SetupKws,
    )


def get_binary():
    libpath = build_pdfium.find_lib(directory=PlatformDirs.SourceBuild)
    return os.path.basename(libpath)


def main():
    libname = get_binary()
    build(lambda: lib_setup(libname), PlatformDirs.SourceBuild)


if __name__ == '__main__':
    main()
