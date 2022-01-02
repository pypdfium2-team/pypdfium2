#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from setup_base import *

class bdist (BDistBase):
    def finalize_options(self):
        BDistBase.finalize_options(self)
        self.plat_name = 'win_arm64'

def lib_setup():
    setuptools.setup(
        cmdclass = {'bdist_wheel': bdist},
        package_data = {'': ['pdfium.dll']},
    )

if __name__ == '__main__':
    build(lib_setup, WindowsArm64)
