#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

set -v

python3 -m pip install . -v --no-build-isolation
rm -f data/.presetup_done.txt
pushd src/pypdfium2/
rm -f _pypdfium.py pdfium pdfium.dll pdfium.dylib
popd
