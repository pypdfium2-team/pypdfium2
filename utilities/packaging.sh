#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

set -v

bash utilities/clean.sh
bash utilities/check.sh

# calling update_pdfium is not actually necessary, but could be done to outsource binary download & bindings generation, rather than doing it within `build` calls
# python3 setupsrc/pypdfium2_setup/update_pdfium.py
python3 setupsrc/pypdfium2_setup/craft_packages.py

twine check dist/*
# ignore W002: erroneous detection of __init__.py files as duplicates
check-wheel-contents dist/*.whl --ignore W002
