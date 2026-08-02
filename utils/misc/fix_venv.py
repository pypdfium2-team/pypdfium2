import sys
from pathlib import Path

VENV_ROOT = Path(sys.argv[1]).resolve()
IS_WINDOWS = sys.platform.startswith("win32")
VENV_BIN = VENV_ROOT / ("Scripts" if IS_WINDOWS else "bin")
assert VENV_ROOT.exists(), f"{VENV_ROOT} does not exist"
assert VENV_BIN.exists(), f"{VENV_BIN} does not exist"

if IS_WINDOWS:
    python_exe = VENV_BIN/"python.exe"
    pip_exe = VENV_BIN/"pip.exe"
    python3_exe = VENV_BIN/"python3.exe"
    pip3_exe = VENV_BIN/"pip3.exe"
    
    assert python_exe.exists(), "python.exe must exist"
    assert pip_exe.exists(), "pip.exe must exist"
    
    if not python3_exe.exists():
        python3_exe.symlink_to(python_exe)
    if not pip3_exe.exists():
        pip3_exe.symlink_to(pip_exe)

print(str(VENV_BIN), end="")
