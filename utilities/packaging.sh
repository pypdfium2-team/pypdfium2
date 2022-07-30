#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

set -v

bash utilities/clean.sh
bash utilities/check.sh

bash utilities/install.sh
python3 -m pytest tests/

python3 ./setupsrc/pl_setup/update_pdfium.py
python3 ./setupsrc/pl_setup/craft_packages.py

twine check dist/*
check-wheel-contents dist/*.whl
