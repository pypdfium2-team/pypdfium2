#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import build as build_pdfium
from setup_base import *
import setup_source


class DefaultArgs:
    argfile = None
    srcname = None
    destname = None
    update = False


if __name__ == '__main__':
    build_pdfium.main(DefaultArgs)
    setup_source.main()
