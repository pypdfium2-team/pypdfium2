#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# check for unused imports
importchecker src/
importchecker tests/
for pyfile in *.py; do importchecker "$pyfile"; done

bash utilities/clean.sh
python3 update_pdfium.py
bash utilities/setup_all.sh
twine check dist/*
check-wheel-contents dist/*.whl
