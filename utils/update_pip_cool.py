# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import re
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from simplebase import ProjectDir, log, get_cool_date

LockDir = ProjectDir/"lock"
LockDir_Pip = LockDir/"unmanaged"/"pip"

def run(cmd, check=True, **kwargs):
    log(cmd)
    return subprocess.run(cmd, check=check, **kwargs)

def get_version(cmd, progname):
    p = run(cmd, stdout=subprocess.PIPE)
    output = p.stdout.decode()
    version = re.search(fR"{progname} ([\d.]+)", output, flags=re.IGNORECASE).group(1)
    return tuple(int(v) for v in version.split("."))

pip_version = get_version([sys.executable, "-m", "pip", "--version"], "pip")
pip_major = pip_version[0]
log(f"pip version is {pip_version}")

# Try to obtain a pip version that honors cooldown before updating pip unbounded
# NOTE: We're always using lockfiles here, because for some reason pip supports --hash in requirements files earlier than it does on a normal pip install command.
update_ok = True
if pip_major < 26:
    py_version = sys.version_info[:2]
    log(f"Python version is {tuple(py_version)}")
    if py_version >= (3, 10):
        pip_lock = LockDir/"pip.txt"
    elif py_version >= (3, 6):
        pip_lock = LockDir_Pip/f"py{py_version[0]}{py_version[1]}.txt"
        update_ok = py_version >= (3, 9)
        if not update_ok:
            log("WARNING: Max known pip version does not support dependency cooldown. Will not attempt to update pip further.")
    else:
        raise ValueError("Unsupported Python version below 3.6 - don't know max pip version.")
    if pip_lock:
        run([sys.executable, "-m", "pip", "install", "--no-deps", "--require-hashes", "-r", str(pip_lock)])

if update_ok:
    run([sys.executable, "-m", "pip", "install", "--uploaded-prior-to", get_cool_date(3), "-U", "pip"])
