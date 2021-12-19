#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

python3 setup_darwin_x64.py   bdist_wheel
python3 setup_darwin_arm64.py bdist_wheel
python3 setup_linux_x64.py    bdist_wheel
python3 setup_linux_arm64.py  bdist_wheel
python3 setup_linux_arm32.py  bdist_wheel
python3 setup_windows_x64.py  bdist_wheel
python3 setup_windows_x86.py  bdist_wheel
python3 setup_sdist.py sdist
