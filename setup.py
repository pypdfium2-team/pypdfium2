#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import build as build_pdfium
from setup_base import *
from setup_source import bdist, lib_setup, get_binary


class DefaultArgs:
    argfile = None
    srcname = None
    destname = None
    update = False


if __name__ == '__main__':
    
    build_pdfium.main(DefaultArgs)
    
    libname = get_binary()
    
    build(lambda: lib_setup(libname), build_pdfium.OutputDir)
    binary_path = join(SourceTree, 'src', 'pypdfium2', libname)
    os.remove(binary_path)
