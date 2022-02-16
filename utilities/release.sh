#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

echo "Cleaning up..."
bash utilities/clean.sh

echo "Running checks..."
bash utilities/check.sh

echo "Installing library locally..."
bash utilities/install.sh
echo "Running test suite..."
python3 -m pytest tests/

echo "Downloading binaries..."
python3 platform_setup/update_pdfium.py
echo "Creating packages..."
bash utilities/setup_all.sh

echo "Confirming validity of generated packages..."
twine check dist/*
check-wheel-contents dist/*.whl
