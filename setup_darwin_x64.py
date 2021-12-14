#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from setup_base import *

class bdist (BDistBase):
    def finalize_options(self):
        BDistBase.finalize_options(self)
        self.plat_name = 'macosx_10_11_x86_64'

def lib_setup():
    setuptools.setup(
        cmdclass = {'bdist_wheel': bdist},
        package_data = {'': ['pdfium.dylib']},
    )

if __name__ == '__main__':
    build(lib_setup, Darwin64)
