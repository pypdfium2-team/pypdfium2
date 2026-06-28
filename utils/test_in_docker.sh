# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

set -exuo pipefail

WHEELFILE="$1"
eval "$PREPARE_CMD"
# alternatively: python3 -m pip config set global.break-system-packages true
python3 -m venv --system-site-packages testenv
VENV_ROOT="/testenv"
VENV_PY="$VENV_ROOT/bin/python3"
PYPDFIUM_DIR="/pypdfium2"
CPUNAME=$(uname -m)

$VENV_PY -m pip install -U pip
cd "$PYPDFIUM_DIR"
# In mips64le/debian docker, `uname -m` says just "mips64"
if [ "$CPUNAME" == "mips64" ]; then
    # https://github.com/pypa/pip/issues/14095
    $VENV_PY -m pip install -U wheel
    bash "$PYPDFIUM_DIR/utils/enforce_install.sh" "$WHEELFILE" "$VENV_PY"
else
    $VENV_PY -m pip install "$WHEELFILE"
fi

$VENV_PY -m pytest tests/
