#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Author's note: This basically replicates a small chunk of what cibuildwheel does internally. I'm starting to really see what cibuildwheel exists for...

import sys
import shlex
import argparse
import subprocess
from pathlib import Path

UTILS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = UTILS_DIR.parent

def log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

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

def run(cmd):
    cmd = archprefix + cmd
    log(cmd)
    subprocess.run(cmd, check=True, cwd=PROJECT_DIR)

errors = {}
for py_ver in reversed(args.py_vers):
    
    python = f"python{py_ver}"
    bin_dir = Path()
    if args.venv:
        venv_name = f"testenv_{py_ver}" + ("_emu" if archprefix else "")
        run([python, "-m", "venv", venv_name, "--clear"])
        bin_dir = Path(venv_name)/"bin"
        python = str(bin_dir/"python")
    if archprefix:
        run([python, "-c", "import platform as p; print(p.machine())"])
    
    run([python, "-m", "pip", "install", args.wheel_path])
    run([python, "-m", "pip", "install", "-U", "-r", "req/test.txt"])
    try:
        run([str(bin_dir/"pypdfium2"), "--version"])
        run([python, "-m", "pytest", "tests/"])
    except subprocess.CalledProcessError as e:
        errors[py_ver] = e.returncode
    else:
        errors[py_ver] = 0

log(errors)
if any(e != 0 for e in errors.values()):
    sys.exit(1)
