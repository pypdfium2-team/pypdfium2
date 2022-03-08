#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

set -v

# build wheels
whl_targets=(
    "darwin_arm64"
    "darwin_x64"
    "linux_arm64"
    "linux_arm32"
    "linux_x64"
    "linux_x86"
    "windows_arm64"
    "windows_x64"
    "windows_x86"
)
for target in ${whl_targets[*]}; do
    echo "$target"
    PYP_TARGET_PLATFORM="$target" python3 -m build -n -x --wheel
done

# package source distribution
PYP_TARGET_PLATFORM="sdist" python3 -m build -n -x --sdist
