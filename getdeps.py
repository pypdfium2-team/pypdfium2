#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

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
SysDeps = [
    'gcc',
    'git',
]

def install_ctypesgen():
    
    if exists(Ctypesgen_Dir):
        run_cmd(f"git reset --hard HEAD", cwd=Ctypesgen_Dir)
        run_cmd(f"git pull", cwd=Ctypesgen_Dir)
    else:
        run_cmd(f"git clone {Ctypesgen_URL}", cwd=SB_Dir)
    
    run_cmd(f"pip3 install -U . -v", cwd=Ctypesgen_Dir)


def install_pydeps():
    for dep in PyDeps:
        run_cmd(f"pip3 install {dep}", cwd=None)


def check_sysdeps():
    
    for dep_name in SysDeps:
        
        dep_binary = shutil.which(dep_name)
        
        if dep_binary is None:
            print(
                f"Missing system dependency: {dep_name} - please install it using your package manager.",
                file = sys.stderr,
            )
        else:
            print(f"Found installation of system dependency {dep_name}")


def main():
    check_sysdeps()
    install_pydeps()
    install_ctypesgen()


if __name__ == '__main__':
    main()
