# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
from pathlib import Path

VENV_BIN_DIR = Path(sys.argv[1]).resolve()
assert VENV_BIN_DIR.exists()

if sys.platform.startswith("win32"):
    python_exe = VENV_BIN_DIR/"python"
    python3_exe = VENV_BIN_DIR/"python3"
    assert python_exe.exists()
    if not python3_exe.exists():
        python3_exe.symlink_to(python_exe)
        (VENV_BIN_DIR/"pip3").symlink_to(VENV_BIN_DIR/"pip")
