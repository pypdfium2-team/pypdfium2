#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0 

set -v

python3 ./setupsrc/pl_setup/build_pdfium.py
export PYP_TARGET_PLATFORM="sourcebuild"
python3 -m pip install . -v --no-build-isolation
