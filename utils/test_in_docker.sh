# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

set -exuo pipefail

eval "$PREPARE_CMD"

# alternatively: python3 -m pip config set global.break-system-packages true
python3 -m venv --system-site-packages testenv
VENV_ROOT="/testenv"
VENV_PY="$VENV_ROOT/bin/python3"
PYPDFIUM_DIR="/pypdfium2"
WHEEL_PATH="./wheelhouse/*.whl"

cd "$PYPDFIUM_DIR"
CPUNAME=$(uname -m)
# In mips64le/debian docker, `uname -m` says just "mips64"
if [ "$CPUNAME" == "mips64" ]; then
    # On MIPS, `pip install` appears to refuse platform wheels, no matter if the tag is "mips64le", "mips64" (matching uname) or whatever. Use this hack to install anyway.
    bash "$PYPDFIUM_DIR/utils/enforce_install.sh" "$VENV_ROOT" "manylinux_2_17_mips64le" $WHEEL_PATH
else
    $VENV_PY -m pip install $WHEEL_PATH
fi

$VENV_PY -m pytest tests/
