# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
from pathlib import Path

VENV_BIN_DIR = Path(sys.argv[1]).resolve()
assert VENV_BIN_DIR.exists()

if sys.platform.startswith("win32"):
    python_exe = VENV_BIN_DIR/"python.exe"
    pip_exe = VENV_BIN_DIR/"pip.exe"
    python3_exe = VENV_BIN_DIR/"python3.exe"
    pip3_exe = VENV_BIN_DIR/"pip3.exe"
    assert python_exe.exists() and pip_exe.exists()
    if not python3_exe.exists():
        python3_exe.symlink_to(python_exe)
    if not pip3_exe.exists():
        pip3_exe.symlink_to(pip_exe)
