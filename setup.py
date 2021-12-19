#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import setup_source
import build_pdfium


class DefaultArgs:
    argfile  = None
    srcname  = None
    destname = None
    update   = False


if __name__ == '__main__':
    build_pdfium.main(DefaultArgs)
    setup_source.main()
