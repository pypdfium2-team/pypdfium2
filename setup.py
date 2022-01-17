#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import setup_source
import build_pdfium

sb_argv = [
    '--getdeps',
]

if __name__ == '__main__':
    args = build_pdfium.parse_args(sb_argv)
    build_pdfium.main(args)
    setup_source.main()
