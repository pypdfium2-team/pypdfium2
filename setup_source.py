#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import os
import distutils.util
from setup_base import *
import sourcebuild


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


if __name__ == '__main__':
    
    libname = sourcebuild.main()
    build(lambda: lib_setup(libname), SourceBuild)
    
    binary = join(SourceTree,'src','pypdfium2',libname)
    os.remove(binary)
