#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import shutil
from _packaging import run_cmd


PyDeps = [
    'ctypesgen',
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


def install_pydeps():
    for dep in PyDeps:
        run_cmd("python3 -m pip install {}".format(dep), cwd=None)


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


if __name__ == '__main__':
    main()
