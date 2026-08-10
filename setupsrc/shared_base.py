# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("ProjectDir", "log", "get_cool_date", "install_dep_groups")

import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from importlib import import_module


ProjectDir = Path(__file__).resolve().parents[1]

def log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

def get_cool_date(cooldown_days):
    return (datetime.now(timezone.utc) - timedelta(days=cooldown_days)).isoformat(timespec='seconds')

# TODO rename & make public? or replace with run_cmd() from base.py?
def _run(cmd, check=True, **kwargs):
    log(cmd)
    subprocess.run(cmd, check=check, **kwargs)


# Work around python 3.8's max pip being too old for PEP 735 dependency groups

def _import_with_fallback(*candidates):
    for candidate in candidates:
        try:
            module = import_module(candidate)
        except ImportError:
            continue
        else:
            return module

def _parse_dep_group(raw_groups, key):
    group = []
    for entry in raw_groups[key]:
        if isinstance(entry, str):
            group.append(entry)
        else:
            group.extend(_parse_dep_group(raw_groups, entry["include-group"]))
    return group

_DEPGROUP_FALLBACK = sys.version_info < (3, 9)
tomllib = _import_with_fallback("tomllib", "tomli")

def install_dep_groups(groups, python=sys.executable, need_fallback=_DEPGROUP_FALLBACK, prefix=()):
    
    assert tomllib, "No toml library found. You want to install tomli, or use python >= 3.11 as dispatcher."
    with (ProjectDir/"pyproject.toml").open("rb") as fh:
        pyproject_toml = tomllib.load(fh)
    
    pip_args = []
    if need_fallback:
        for group in groups:
            pip_args.extend( _parse_dep_group(pyproject_toml["dependency-groups"], group) )
    else:
        for group in groups:
            pip_args.extend(("--group", group))
    
    _run([*prefix, python, "-m", "pip", "install", "-U", *pip_args])
