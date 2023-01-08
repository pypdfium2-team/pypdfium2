#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

set -v

bash utilities/clean.sh
bash utilities/check.sh

python3 setupsrc/pl_setup/update_pdfium.py
python3 setupsrc/pl_setup/craft_wheels.py

twine check dist/*
# ignore W002: erroneous detection of __init__.py files as duplicates
check-wheel-contents dist/*.whl --ignore W002
