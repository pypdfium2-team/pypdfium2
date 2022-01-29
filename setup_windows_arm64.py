#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from _setup_base import *

class bdist (BDistBase):
    def finalize_options(self):
        BDistBase.finalize_options(self)
        self.plat_name = 'win_arm64'

def lib_setup():
    setuptools.setup(
        cmdclass = {'bdist_wheel': bdist},
        package_data = {'': ['pdfium.dll']},
        **SetupKws,
    )

def main():
    return build(lib_setup, PlatformDirs.WindowsArm64)

if __name__ == '__main__':
    main()
