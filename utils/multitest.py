#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Author's note: This basically replicates a small chunk of what cibuildwheel does internally. I'm starting to really see what cibuildwheel exists for...

import re
import os
import sys
import shlex
import platform
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from base import ProjectDir, log, get_cool_date

IS_WINDOWS = sys.platform.startswith("win32")
PYTHON_EXE = "python" + (".exe" if IS_WINDOWS else "")
WINDOWS_32BIT = bool(int( os.environ.get("WINDOWS_32BIT", 0) ))


# work around https://github.com/actions/setup-python/issues/1079
def _get_python_exe_map():
    
    exemap = {}
    if not (sys.platform.startswith("win32") and bool(os.getenv("GITHUB_ACTIONS"))):
        return exemap
    
    cpu_id = platform.machine().lower()
    if WINDOWS_32BIT and cpu_id == "amd64":
        cpu_id = "x86"
    else:
        cpu_id = {"amd64": "x64"}.get(cpu_id, cpu_id)  # arm64 and x86 implied
    # cf. https://github.com/actions/setup-python/blob/main/docs/advanced-usage.md#hosted-tool-cache
    install_dir = Path(os.environ["RUNNER_TOOL_CACHE"]) / "Python"
    for subdir in install_dir.iterdir():
        match = re.match(r"(\d.\d*).", subdir.name)
        if not match:
            continue
        exemap[match.group(1)] = str(subdir/cpu_id/PYTHON_EXE)
    
    return exemap


parser = argparse.ArgumentParser(
    description = "Test with multiple python versions",
)
parser.add_argument("-w", "--wheel-path", required=True)
parser.add_argument("--py-vers", nargs="+", required=True)
parser.add_argument("--prefix")
parser.add_argument("--venv", action="store_true")
args = parser.parse_args()

archprefix = []
if args.prefix:
    archprefix = shlex.split(args.prefix)

def run(cmd, **kwargs):
    cmd = archprefix + cmd
    log(cmd)
    subprocess.run(cmd, check=True, cwd=ProjectDir, **kwargs)

PyExeMap = _get_python_exe_map()


errors = {}
for py_ver in reversed(args.py_vers):
    
    python = f"python{py_ver}"
    if PyExeMap:
        python = PyExeMap.get(py_ver, python)
    
    bin_dir = Path()
    if args.venv:
        venv_name = f"testenv_{py_ver}" + ("_emu" if archprefix else "")
        run([python, "-m", "venv", venv_name])
        bin_dir = Path(venv_name) / ("Scripts" if IS_WINDOWS else "bin")
        python = str(bin_dir/PYTHON_EXE)
        # This may or may not be honored (see the notes in install_step/action.yml)
        env = os.environ.copy()
        env["PIP_UPLOADED_PRIOR_TO"] = get_cool_date(3)
        run([python, "-m", "pip", "install", "-U", "pip"], env=env)
    
    pypdfium2_exe = str(bin_dir/"pypdfium2")
    if archprefix:
        run([python, "-c", "import platform as p; print(p.machine())"])
    
    os.environ["PIP_UPLOADED_PRIOR_TO"] = get_cool_date(12)
    run([python, "-m", "pip", "install", args.wheel_path])
    run([python, "-m", "pip", "install", "-U", "-r", "req/test.txt"])
    try:
        run([pypdfium2_exe, "--version"])
        run([python, "-m", "pytest", "tests/"])
    except subprocess.CalledProcessError as e:
        errors[py_ver] = e.returncode
    else:
        errors[py_ver] = 0

log(errors)
if any(e != 0 for e in errors.values()):
    sys.exit(1)
