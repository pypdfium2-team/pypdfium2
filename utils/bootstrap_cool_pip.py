# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import re
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from simplebase import log, get_cool_date

def run(cmd, check=True, **kwargs):
    log(cmd)
    return subprocess.run(cmd, check=check, **kwargs)

def get_version(cmd, progname):
    p = run(cmd, stdout=subprocess.PIPE)
    output = p.stdout.decode()
    version = re.search(fR"{progname} ([\d.]+)", output, flags=re.IGNORECASE).group(1)
    return tuple(int(v) for v in version.split("."))

python = sys.argv[1] if len(sys.argv) > 1 else sys.executable
pip_version = get_version([python, "-m", "pip", "--version"], "pip")
pip_major = pip_version[0]
log(f"Determined pip version {pip_version}")

# try to obtain a pip version that honors cooldown before updating pip unbounded
if pip_major < 26:
    # TODO add hash checking
    py_version = get_version([python, "--version"], "Python")[:2]
    log(f"Determined python version: {py_version}")
    if py_version == (3, 9):
        pip_pin, update_ok = "26.0.1", True
    elif py_version == (3, 8):
        log("WARNING: Python 3.8's max pip does not support dependency cooldowns!")
        pip_pin, update_ok = "25.0.1", False
    else:
        assert py_version >= (3, 10)
        pip_pin, update_ok = "26.1.2", True
    run([python, "-m", "pip", "install", f"pip=={pip_pin}"])
else:
    update_ok = True

if update_ok:
    cool_date = get_cool_date(3)
    run([python, "-m", "pip", "install", "--uploaded-prior-to", cool_date, "-U", "pip"])
