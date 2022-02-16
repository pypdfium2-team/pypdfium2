#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# clean up
bash utilities/clean.sh

# run checks
bash utilities/check.sh

# install project locally and run the test suite
bash utilities/install.sh
python3 -m pytest tests/

# download binaries and create the wheels
python3 platform_setup/update_pdfium.py
bash utilities/setup_all.sh

# ensure validity of the generated wheels
twine check dist/*
check-wheel-contents dist/*.whl
