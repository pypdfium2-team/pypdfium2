#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import shutil
from os.path import (
    join,
    exists,
)
from _packaging import SB_Dir, run_cmd

Ctypesgen_URL = "https://github.com/ctypesgen/ctypesgen.git"
Ctypesgen_Dir = join(SB_Dir,'ctypesgen')

PyDeps = [
    'setuptools',
    'wheel',
]
SysCommands = [
    'git',
    'gcc',
]
NB_SysCommands = [
    'gn',
    'ninja',
    'lld',
]

def install_ctypesgen():
    
    # prefer latest ctypesgen from git
    
    if exists(Ctypesgen_Dir):
        run_cmd(f"git reset --hard HEAD", cwd=Ctypesgen_Dir)
        run_cmd(f"git pull", cwd=Ctypesgen_Dir)
    else:
        run_cmd(f"git clone {Ctypesgen_URL}", cwd=SB_Dir)
    
    run_cmd(f"pip3 install -U . -v", cwd=Ctypesgen_Dir)


def install_pydeps():
    for dep in PyDeps:
        run_cmd(f"pip3 install {dep}", cwd=None)


def _notify_found_sysdep(dep_name):
    print(f"Found installation of system dependency {dep_name}")

def _notify_missing_sysdep(dep_name):
    print(
        f"Missing system dependency: {dep_name} - please install it using your package manager.",
        file = sys.stderr,
    )


def check_sysdeps(sys_commands):
    
    for dep_name in sys_commands:
        
        dep_binary = shutil.which(dep_name)
        
        if dep_binary is None:
            _notify_missing_sysdep(dep_name)
        else:
            _notify_found_sysdep(dep_name)


def check_clang(st_prefix):
    
    binaries = os.listdir(st_prefix)
    
    clang = 'clang'
    if any(b.startswith(clang) for b in binaries):
        _notify_found_sysdep(clang)
    else:
        _notify_missing_sysdep(clang)


def main(
        prefer_st = False,
        st_prefix = '/usr/bin',
    ):
    
    sys_commands = SysCommands.copy()
    if prefer_st:
        sys_commands += NB_SysCommands
        check_clang(st_prefix)
    
    check_sysdeps(sys_commands)
    install_pydeps()
    install_ctypesgen()


if __name__ == '__main__':
    main()
