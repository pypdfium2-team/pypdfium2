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

# NOTE Setuptools may run this code several times (if using PEP 517 style setup).

LockFile = join(DataTree, ".lock_autoupdate.txt")


def install_handler():
    
    from pl_setup import update_pdfium
    from pl_setup.setup_base import mkwheel
    
    pl_name = Host.platform
    if pl_name is None:
        # If PDFium had a proper build system, we could trigger a source build here
        raise RuntimeError(
            "No pre-built binaries available for platform '%s' with libc implementation '%s'. " % (Host._plat_info, Host._libc_info) +
            "You can attempt a source build, but it's unlikely to work out due to binary toolchain requirements of PDFium's build system. Doing cross-compilation or using a different build system might be possible, though. Please get in touch with the project maintainers."
        )
    
    
    need_update = False
    
    if not all(exists(fp) for fp in get_platfiles(pl_name)):
        need_update = True  # always update if platform files are missing
    
    elif not exists(LockFile):
        
        # Automatic updates imply some duplication across different runs. The code runs quickly enough, so this is not much of a problem.
        
        latest_ver = get_latest_version()
        ver_file = join(DataTree, pl_name, VerStatusFileName)
        assert os.path.exists(ver_file)
        
        with open(ver_file, "r") as fh:
            curr_version = int( fh.read().strip() )
        assert not curr_version > latest_ver
        
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
        # As check_deps needs to run only once and then never again, we could prevent repeated runs using a status file. However, it runs quickly enough, so this is not really necessary.
        check_deps.main()
        install_handler()
    else:
        packaging_handler(target)


if __name__ == "__main__":
    main()
