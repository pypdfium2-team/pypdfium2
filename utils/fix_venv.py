import sys
from pathlib import Path

VENV_BIN = Path(sys.argv[1])
assert VENV_BIN.is_absolute(), "VENV_BIN must be absolute"
assert VENV_BIN.exists(), "VENV_BIN must exist"

if sys.platform.startswith("win32"):
    
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
