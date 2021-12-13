#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

rm -r dist
rm -r build
rm -r data/*
touch data/.gitkeep
rm -r src/pypdfium2.egg-info/
rm -r __pycache__
rm -r src/pypdfium2/__pycache__
unlink src/pypdfium2/_pypdfium.py
unlink src/pypdfium2/pdfium
unlink src/pypdfium2/pdfium.dll
unlink src/pypdfium2/pdfium.dylib
