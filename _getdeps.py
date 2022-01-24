#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import shutil
from os.path import (
    join,
    exists,
)
from _packaging import (
    SB_Dir,
    run_cmd,
)


Ctypesgen_URL = "https://github.com/ctypesgen/ctypesgen.git"
Ctypesgen_PIN = "cef9a7ac58a50d0ae4f260abdeb75e0a71398187"
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
    'clang',
    'lld',
]


def install_ctypesgen():
    
    # prefer a newer version of ctypesgen
    
    if exists(Ctypesgen_Dir):
        run_cmd("git reset --hard HEAD", cwd=Ctypesgen_Dir)
        run_cmd("git pull {} master".format(Ctypesgen_URL), cwd=Ctypesgen_Dir)
    else:
        run_cmd("git clone {}".format(Ctypesgen_URL), cwd=SB_Dir)
    
    run_cmd("git checkout {}".format(Ctypesgen_PIN), cwd=Ctypesgen_Dir)
    run_cmd("pip3 install -U . -v", cwd=Ctypesgen_Dir)


def install_pydeps():
    for dep in PyDeps:
        run_cmd("pip3 install {}".format(dep), cwd=None)


def check_sysdeps(sys_commands):
    
    for dep_name in sys_commands:
        
        dep_binary = shutil.which(dep_name)
        
        if dep_binary is None:
            print(
                "Missing system dependency: {} - please install it using your package manager.".format(dep_name),
                file = sys.stderr,
            )
        else:
            print("Found installation of system dependency {}".format(dep_name))


def main(prefer_st=False):
    
    sys_commands = SysCommands.copy()
    if prefer_st:
        sys_commands += NB_SysCommands
    
    check_sysdeps(sys_commands)
    install_pydeps()
    install_ctypesgen()


if __name__ == '__main__':
    main()
