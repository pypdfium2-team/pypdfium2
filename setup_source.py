#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import os
import distutils.util
from setup_base import *
import build as build_pdfium


class bdist (BDistBase):
    def finalize_options(self):
        BDistBase.finalize_options(self)
        platform = distutils.util.get_platform()
        platform = platform.replace('-','_').replace('.','_')
        self.plat_name = platform


def lib_setup(libname):
    setuptools.setup(
        cmdclass = {'bdist_wheel': bdist},
        package_data = {'': [libname]},
    )


def get_binary():
    libpath = build_pdfium.find_lib(directory=SB_OutputDir)
    return os.path.basename(libpath)


if __name__ == '__main__':
    
    SB_OutputDir = build_pdfium.OutputDir
    libname = get_binary()
    
    build(lambda: lib_setup(libname), SB_OutputDir)
    binary_path = join(SourceTree, 'src', 'pypdfium2', libname)
    os.remove(binary_path)
