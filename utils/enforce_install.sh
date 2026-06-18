#! /usr/bin/env bash
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# See the comment in test_in_docker.sh for why we need this.

set -exuo pipefail

VENV_ROOT="$1"
PLATFORM_TAG="$2"
WHEEL_PATH="$3"

STAGING_DIR="/tmp/staging"
VENV_PY="$VENV_ROOT/bin/python3"
PY_VERSION=$($VENV_PY -c 'import sys; v = sys.version_info; print(f"{v.major}.{v.minor}")')
PKGDIR="$VENV_ROOT/lib/python$PY_VERSION/site-packages"

$VENV_PY -m pip install --platform "$PLATFORM_TAG" --no-deps --target "$STAGING_DIR" "$WHEEL_PATH"
ls -l "$STAGING_DIR"
mv $STAGING_DIR/bin/* -t "$VENV_ROOT/bin" && rmdir "$STAGING_DIR/bin"
mv $STAGING_DIR/* -t $PKGDIR
