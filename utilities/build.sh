#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0 

set -v

python3 platform_setup/build_pdfium.py --check-deps
export PYP_TARGET_PLATFORM="sourcebuild"
python3 -m build -n -x --wheel
bash ./utilities/install.sh
