#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import setuptools
from os.path import (
    join,
    abspath,
    dirname,
    exists,
)

sys.path.insert(0, join(dirname(abspath(__file__)), "setupsrc"))
from pl_setup import check_deps
from pl_setup.packaging_base import (
    Host,
    DataTree,
    BinaryTargetVar,
    BinaryTarget_None,
    VerStatusFileName,
    PlatformNames,
    get_platfiles,
    get_latest_version,
)

# NOTE Setuptools may, unfortunately, run this code several times (if using PEP 517 style setup).

LockFile = join(DataTree, ".lock_autoupdate.txt")


def install_handler():
    
    from pl_setup import update_pdfium
    from pl_setup.setup_base import mkwheel
    
    pl_name = Host.platform
    if pl_name is None:
        # If PDFium had a proper build system, we could trigger a source build here
        libc_msg = ""
        if Host._libc_info is not None:
            libc_msg = " (libc info %s)" % (Host._libc_info, )
        raise RuntimeError(
            "No pre-built binaries available for system '%s' on machine '%s'" % (Host._system_name, Host._machine_name) + libc_msg + ". " +
            "You may place custom binaries & bindings in data/sourcebuild and install with `%s=sourcebuild`." % (BinaryTargetVar, )
        )
    
    
    need_update = False
    pl_dir = join(DataTree, pl_name)
    ver_file = join(pl_dir, VerStatusFileName)
    
    if not os.path.exists(pl_dir):
        need_update = True  # platform directory doesn't exist yet
    elif not os.path.exists(ver_file) or not all(exists(fp) for fp in get_platfiles(pl_name)):
        print("Warning: Specific platform files are missing -> implicit update", file=sys.stderr)
        need_update = True
    
    elif not exists(LockFile):
        
        # Automatic updates imply some duplication across different runs. The code runs quickly enough, so this is not much of a problem.
        
        latest_ver = get_latest_version()
        with open(ver_file, "r") as fh:
            curr_version = int( fh.read().strip() )
        
        if curr_version > latest_ver:
            raise RuntimeError("Current version must not be greater than latest")
        if curr_version < latest_ver:
            need_update = True
    
    if need_update:
        update_pdfium.main([pl_name])
    mkwheel(pl_name)


def packaging_handler(target):
    
    from pl_setup.setup_base import mkwheel, SetupKws
    
    if target == BinaryTarget_None:
        setuptools.setup(**SetupKws)
    elif hasattr(PlatformNames, target):
        mkwheel( getattr(PlatformNames, target) )
    else:
        raise ValueError("Invalid deployment target '%s'" % target)
    
    return False


def main():
    
    target = os.environ.get(BinaryTargetVar, None)
    
    if target in (None, "auto"):
        # As check_deps should only need to be run once, we could prevent repeated runs using a status file. However, it runs quickly enough, so this isn't necessary.
        check_deps.main()
        install_handler()
    else:
        packaging_handler(target)


if __name__ == "__main__":
    main()
