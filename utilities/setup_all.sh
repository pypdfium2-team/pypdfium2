#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

python3 platform_setup/setup_sdist.py sdist
python3 platform_setup/setup_darwin_x64.py    bdist_wheel
python3 platform_setup/setup_darwin_arm64.py  bdist_wheel
python3 platform_setup/setup_linux_x64.py     bdist_wheel
python3 platform_setup/setup_linux_arm64.py   bdist_wheel
python3 platform_setup/setup_linux_arm32.py   bdist_wheel
python3 platform_setup/setup_windows_x64.py   bdist_wheel
python3 platform_setup/setup_windows_x86.py   bdist_wheel
python3 platform_setup/setup_windows_arm64.py bdist_wheel
