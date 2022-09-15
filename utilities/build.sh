#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0 

set -v

python3 ./setupsrc/pl_setup/build_pdfium.py
PDFIUM_BINARY="sourcebuild" python3 -m pip install -v --no-build-isolation .
