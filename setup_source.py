#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import os
from setup_base import *
from wheel.bdist_wheel import bdist_wheel
from sourcebuild import main as sourcebuild_main


def lib_setup(libname):
    setuptools.setup(
        cmdclass = {'bdist_wheel': bdist_wheel},
        package_data = {'': [libname]},
    )


if __name__ == '__main__':
    
    libname = sourcebuild_main()
    build(lambda: lib_setup(libname), SourceBuild)
    
    binary = join(SourceTree,'src','pypdfium2',libname)
    os.remove(binary)
