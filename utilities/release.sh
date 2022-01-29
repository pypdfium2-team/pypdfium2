#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# clean up
bash utilities/clean.sh

# check for unused imports
importchecker src/
importchecker tests/
for pyfile in *.py; do importchecker "$pyfile"; done

# check for possible spelling mistakes
codespell --skip="./sourcebuild,./docs/build,./data,./.git,__pycache__,.mypy_cache,"

# download binaries and create the wheels
python3 update_pdfium.py
bash utilities/setup_all.sh

# ensure validity of the generated wheels
twine check dist/*
check-wheel-contents dist/*.whl
