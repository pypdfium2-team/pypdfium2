#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import shutil
import importlib.util
from os.path import abspath, dirname

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from pl_setup.packaging_base import run_cmd


PyPackages = (
    "build",
    "wheel",
    "ctypesgen",
    "setuptools",
    "setuptools-scm",
)
SysCommands = (
    "git",
    "gcc",
)


def _pip_install(pkg):
    run_cmd([sys.executable, "-m", "pip", "install", pkg], cwd=None)


def install_pydeps():
    
    for pkg in PyPackages:
        if not importlib.util.find_spec( pkg.replace("-", "_") ):
            _pip_install(pkg)
    
    # Uninstalling ctypesgen sometimes leaves parts behind. In this case, `find_spec()` would still consider the library installed, although the command is unavailable.
    if not shutil.which("ctypesgen"):
        _pip_install("ctypesgen")


def check_sysdeps(sys_commands):
    
    missing = []
    found = []
    
    for dep_name in sys_commands:
        if shutil.which(dep_name):
            found.append(dep_name)
        else:
            missing.append(dep_name)
    
    print("Found system dependencies: %s" % found)
    if len(missing) > 0:
        print("Missing system dependencies: %s" % missing)


def main():
    check_sysdeps(SysCommands)
    install_pydeps()


if __name__ == "__main__":
    main()
