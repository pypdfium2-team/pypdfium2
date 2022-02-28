#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import shutil
from importlib.util import find_spec
from platform_setup.packaging_base import run_cmd

PyPackages = (
    'build',
    'wheel',
    'ctypesgen',
    'setuptools',
    'setuptools-scm',
)
SysCommands = (
    'git',
    'gcc',
)
NB_SysCommands = (
    'gn',
    'ninja',
    'clang',
    'lld',
)


def _pip_install(pkg):
    exe = sys.executable
    if not exe:
        exe = "python3"
    run_cmd('"{}" -m pip install "{}"'.format(exe, pkg), cwd=None)


def install_pydeps():
    
    for pkg in PyPackages:
        if not find_spec( pkg.replace('-', '_') ):
            _pip_install(pkg)
    
    # uninstalling ctypesgen sometimes leaves parts behind, which makes the command unavailable,
    # but `find_spec()` would still consider the library installed
    if not shutil.which('ctypesgen'):
        _pip_install('ctypesgen')


def check_sysdeps(sys_commands):
    
    missing = []
    found = []
    
    for dep_name in sys_commands:
        if shutil.which(dep_name):
            found.append(dep_name)
        else:
            missing.append(dep_name)
    
    print( "Found system dependencies: {}".format(found) )
    if len(missing) > 0:
        print( "Missing system dependencies: {}".format(missing) )


def main(prefer_st=False):
    
    sys_commands = SysCommands
    if prefer_st:
        sys_commands += NB_SysCommands
    
    check_sysdeps(sys_commands)
    install_pydeps()


if __name__ == '__main__':
    main()
