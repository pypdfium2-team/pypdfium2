#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# See the comment in inside_docker.sh for why we need this.

set -exuo pipefail

WHEEL_PATH="$1"
PYTHON="$2"
WHEEL_DIR=$(dirname $WHEEL_PATH)

HOST_PLATFORM=$($PYTHON -c "import sysconfig; print(sysconfig.get_platform())")
RETAGGED_WHEEL_NAME=$($PYTHON -m wheel tags --platform-tag=linux_mips64 $WHEEL_PATH)
$PYTHON -m pip install -v $WHEEL_DIR/$RETAGGED_WHEEL_NAME
