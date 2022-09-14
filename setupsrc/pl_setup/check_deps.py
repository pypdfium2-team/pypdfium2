#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import shutil
import importlib.util


Packages = (
    "build",
    "wheel",
    "ctypesgen",
    "setuptools",
)
Commands = (
    "git",
    "gcc",
    "ctypesgen",
)


have_package = lambda pkg: importlib.util.find_spec( pkg.replace("-", "_") )


def main():
    
    missing_pkgs = {pkg for pkg in Packages if not have_package(pkg)}
    missing_cmds = {cmd for cmd in Commands if not shutil.which(cmd)}
    missing = missing_pkgs.union(missing_cmds)
    
    if len(missing) > 0:
        raise RuntimeError("The following packages or commands are missing: %s" % missing)


if __name__ == "__main__":
    main()
