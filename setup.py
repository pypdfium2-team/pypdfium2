#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import setuptools
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "setupsrc"))
from pypdfium2_setup.packaging_base import (
    Host,
    DataTree,
    VersionTargetVar,
    BinaryTargetVar,
    BinaryTarget_None,
    VerStatusFileName,
    PlatformNames,
    get_platfiles,
    get_latest_version,
)

# NOTE setuptools may, unfortunately, run this code several times (if using PEP 517 style setup).


def install_handler():
    
    # TODO Linux/macOS: check that minimum OS version requirements are fulfilled
    
    # FIXME not really necessary?
    from pypdfium2_setup import check_deps
    check_deps.main()
    
    from pypdfium2_setup import update_pdfium
    from pypdfium2_setup.setup_base import mkwheel
    
    pl_name = Host.platform
    if pl_name is None:
        # If PDFium had a proper build system, we could trigger a source build here
        raise RuntimeError(f"No pre-built binaries available for system {Host._system_name} (libc info {Host._libc_info}) on machine {Host._machine_name}. You may place custom binaries & bindings in data/sourcebuild and install with `{BinaryTargetVar}=sourcebuild`.")
    
    pl_dir = DataTree / pl_name
    ver_file = pl_dir / VerStatusFileName
    
    curr_ver = None
    if ver_file.exists() and all(fp.exists() for fp in get_platfiles(pl_name)):
        curr_ver = int( ver_file.read_text().strip() )
    
    req_ver = os.environ.get(VersionTargetVar, None)
    if req_ver in (None, "", "latest"):
        req_ver = get_latest_version()
    else:
        req_ver = int(req_ver)
    
    if curr_ver != req_ver:
        print(f"Switching pdfium binary from {curr_ver} to {req_ver}", file=sys.stderr)
        update_pdfium.main([pl_name], version=req_ver)
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
        install_handler()
    else:
        packaging_handler(target)


if __name__ == "__main__":
    main()
