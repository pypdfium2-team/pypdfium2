# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

eval "$PREPARE_CMD"
# alternatively: python3 -m pip config set global.break-system-packages true
python3 -m venv --system-site-packages testenv
VENV_PY=/testenv/bin/python3
cd /pypdfium2
$VENV_PY -m pip install ./wheelhouse/*.whl
$VENV_PY -m pytest tests/
