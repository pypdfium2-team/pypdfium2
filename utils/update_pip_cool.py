# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import re
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from simplebase import ProjectDir, log, get_cool_date

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

# try to obtain a pip version that honors cooldown before updating pip unbounded
pass_cooldown = True
if pip_major < 26:
    py_version = sys.version_info[:2]
    log(f"Python version is {py_version}")
    # NOTE: we're always using lockfiles here, because for some reason pip supports --hash in requirements files earlier than it does on a normal pip install command
    if py_version >= (3, 10):
        pip_lock, update_ok = "py_current", True
    elif py_version == (3, 9):
        pip_lock, update_ok = "py_39", True
    elif py_version == (3, 8):
        pip_lock, update_ok = "py_38", False
    # TODO handle 3.7 (what is its max pip version?)
    elif py_version == (3, 6):
        pip_lock, update_ok = "py_36", False
    else:
        pip_lock, update_ok, pass_cooldown = None, True, False
        log("WARNING: Unhandled python version - don't have a pip pin. Will proceed with unsafe update to the max pip version. Dependency cooldowns will not be supported!")
    if pip_lock:
        run([sys.executable, "-m", "pip", "install", "--no-deps", "--require-hashes", "-r", str(ProjectDir/"lock"/"pip"/f"{pip_lock}.txt")])
    if not update_ok:
        log("WARNING: Max known pip version does not support dependency cooldown. Will not attempt to update pip further.")
else:
    update_ok = True

if update_ok:
    cooldown_args = ("--uploaded-prior-to", get_cool_date(3)) if pass_cooldown else ()
    run([sys.executable, "-m", "pip", "install", *cooldown_args, "-U", "pip"])
