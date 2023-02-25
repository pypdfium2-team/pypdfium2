#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import setuptools
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "setupsrc"))
from pypdfium2_setup import check_deps
from pypdfium2_setup.packaging_base import (
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

LockFile = DataTree / ".lock_autoupdate.txt"


def install_handler():
    
    from pypdfium2_setup import update_pdfium
    from pypdfium2_setup.setup_base import mkwheel
    
    pl_name = Host.platform
    if pl_name is None:
        # If PDFium had a proper build system, we could trigger a source build here
        raise RuntimeError(f"No pre-built binaries available for system {Host._system_name} (libc info {Host._libc_info}) on machine {Host._machine_name}. You may place custom binaries & bindings in data/sourcebuild and install with `{BinaryTargetVar}=sourcebuild`.")
    
    # TODO Linux/macOS: check that minimum version requirements are fulfilled
    
    need_update = False
    pl_dir = DataTree / pl_name
    ver_file = pl_dir / VerStatusFileName
    
    if not pl_dir.exists():
        need_update = True  # platform directory doesn't exist yet
    elif not ver_file.exists() or not all(fp.exists() for fp in get_platfiles(pl_name)):
        print("Warning: Specific platform files are missing -> implicit update", file=sys.stderr)
        need_update = True
    
    elif not LockFile.exists():
        
        # Automatic updates imply some duplication across different runs. The code runs quickly enough, so this is not much of a problem.
        
        latest_ver = get_latest_version()
        curr_version = int( ver_file.read_text().strip() )
        
        if curr_version > latest_ver:
            raise RuntimeError("Current version must not be greater than latest")
        if curr_version < latest_ver:
            need_update = True
    
    if need_update:
        update_pdfium.main([pl_name])
    mkwheel(pl_name)


def packaging_handler(target):
    
    from pypdfium2_setup.setup_base import mkwheel, SetupKws
    
    if target == BinaryTarget_None:
        setuptools.setup(**SetupKws)
    elif hasattr(PlatformNames, target):
        mkwheel( getattr(PlatformNames, target) )
    else:
        raise ValueError(f"Invalid deployment target '{target}'")
    
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
