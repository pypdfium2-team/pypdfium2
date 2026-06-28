#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

set -exuo pipefail

# q&d: infer container target name from wheel name
WHEEL_PATH="$1"
TARGET=$(python3 utils/regextract.py "-(\w+linux)_[\d_]+_(\w+)\." "%s_%s" $(ls $WHEEL_PATH))
echo $TARGET
python3 ./utils/container_driver.py "$TARGET" -w $WHEEL_PATH
