#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import getdeps
import setup_source
import build_pdfium


sb_argv = []

if __name__ == '__main__':
    getdeps.main()
    args = build_pdfium.parse_args(sb_argv)
    build_pdfium.main(args)
    setup_source.main()
