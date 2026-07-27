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
if pip_major < 26:
    py_version = sys.version_info[:2]
    log(f"Python version is {py_version}")
    pass_cooldown = True
    if py_version >= (3, 10):
        pip_lock, update_ok = "py_current", True
    if py_version == (3, 9):
        pip_lock, update_ok = "py_39", True  # supports cooldown
    elif py_version == (3, 8):
        log("WARNING: Python 3.8's max pip does not support dependency cooldowns!")
        pip_lock, update_ok = "py_38", False
    else:
        # Python 3.6 max pip is 21.3.1. Not sure about Python 3.7.
        log("WARNING: Unhandled python version below 3.8. Doing unsafe update to the max pip version. It will not support dependency cooldowns!")
        pip_lock, update_ok = None, True
        pass_cooldown = False
    if pip_lock:
        run([sys.executable, "-m", "pip", "install", "--require-hashes", "--no-deps", "-r", ProjectDir/"lock"/"pip"/f"{pip_lock}.txt"])
else:
    update_ok = True

if update_ok:
    cooldown_args = ("--uploaded-prior-to", get_cool_date(3)) if pass_cooldown else ()
    run([sys.executable, "-m", "pip", "install", *cooldown_args, "-U", "pip"])
