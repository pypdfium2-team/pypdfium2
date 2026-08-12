# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("ProjectDir", "log", "get_cool_date", "install_dep_groups")

import sys
import subprocess
from pathlib import Path
from itertools import chain
from importlib import import_module
from datetime import datetime, timezone, timedelta

ProjectDir = Path(__file__).resolve().parents[1]

# Add this path to your IDE's search path, e.g. VS Code python.analysis.extraPaths
sys.path.insert(0, str(ProjectDir/"src"/"pypdfium2_cfg"/"_shared"))


def log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

def get_cool_date(cooldown_days):
    return (datetime.now(timezone.utc) - timedelta(days=cooldown_days)).isoformat(timespec='seconds')


# TODO rename & make public? or replace with run_cmd() from base.py?
def _run(cmd, check=True, **kwargs):
    log(cmd)
    subprocess.run(cmd, check=check, **kwargs)

def _import_with_fallback(*candidates):
    for candidate in candidates:
        try:
            module = import_module(candidate)
        except ImportError:
            continue
        else:
            return module

def _prepend_each(value, iterable):
    for item in iterable:
        yield value
        yield item


# Work around python 3.8's max pip being too old for PEP 735 dependency groups

def _parse_dep_group(raw_groups, key):
    group = []
    for entry in raw_groups[key]:
        if isinstance(entry, str):
            group.append(entry)
        else:
            group.extend(_parse_dep_group(raw_groups, entry["include-group"]))
    return group

tomllib = _import_with_fallback("tomllib", "tomli")  # TODO make lazy
_DEPGROUP_FALLBACK = tomllib or (sys.version_info < (3, 9))

def install_dep_groups(groups, python=sys.executable, use_fallback=_DEPGROUP_FALLBACK, prefix=(), env=None):
    
    if use_fallback:
        assert tomllib, "No toml library found. You want to install tomli, or use python >= 3.11 as dispatcher."
        with (ProjectDir/"pyproject.toml").open("rb") as fh:
            pyproject_toml = tomllib.load(fh)
        raw_groups = pyproject_toml["dependency-groups"]
        pip_args = chain.from_iterable(_parse_dep_group(raw_groups, k) for k in groups)
    else:
        pip_args = _prepend_each("--group", groups)
    
    _run([*prefix, python, "-m", "pip", "install", "-U", *pip_args], env=env)
