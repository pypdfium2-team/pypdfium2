#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# NOTE setuptools may, unfortunately, run this code several times (if using PEP 517 style setup).

import os
import sys
import setuptools
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "setupsrc"))
# TODO? consider glob import or dotted access
from pypdfium2_setup.packaging_base import (
    Host,
    DataTree,
    BinaryTargetVar,
    BinaryTarget_Auto,
    BinaryTarget_None,
    VersionTargetVar,
    VersionTarget_Latest,
    VerStatusFileName,
    V8StatusFileName,
    PlatformNames,
    set_versions,
    get_platfiles,
    get_latest_version,
)


def install_handler():
    
    # TODO? Linux/macOS: check that minimum OS version requirements are fulfilled
    
    from pypdfium2_setup import update_pdfium
    from pypdfium2_setup.setup_base import mkwheel
    
    pl_name = Host.platform
    if pl_name is None:
        # If PDFium had a proper build system, we could trigger a source build here
        raise RuntimeError(f"No pre-built binaries available for system {Host._system_name} (libc info {Host._libc_info}) on machine {Host._machine_name}. You may place custom binaries & bindings in data/sourcebuild and install with `{BinaryTargetVar}=sourcebuild`.")
    
    pl_dir = DataTree / pl_name
    ver_file = pl_dir / VerStatusFileName
    
    prev_ver = None
    if ver_file.exists() and all(fp.exists() for fp in get_platfiles(pl_name)):
        prev_ver = int( ver_file.read_text().strip() )
    
    new_ver = os.environ.get(VersionTargetVar, None)
    if not new_ver or (new_ver.lower() == VersionTarget_Latest):
        new_ver = get_latest_version()
    else:
        new_ver = int(new_ver)
    
    had_v8 = (pl_dir / V8StatusFileName).exists()
    use_v8 = bool(int( os.environ.get("PDFIUM_USE_V8", 0) ))
    
    if (prev_ver != new_ver) or (had_v8 != use_v8):
        print(f"Switching pdfium binary from {prev_ver} (v8 {had_v8}) to {new_ver} (v8 {use_v8})", file=sys.stderr)
        update_pdfium.main([pl_name], version=new_ver, use_v8=use_v8)
    mkwheel(pl_name)


def packaging_handler(target):
    
    from pypdfium2_setup.setup_base import mkwheel, SetupKws
    
    if target == BinaryTarget_None:
        set_versions( dict(V_LIBPDFIUM="unknown", V_BUILDNAME="unknown", V_PDFIUM_IS_V8=None) )
        setuptools.setup(**SetupKws)
    elif hasattr(PlatformNames, target):
        mkwheel( getattr(PlatformNames, target) )
    else:
        raise ValueError(f"Invalid deployment target '{target}'")


def main():
    target = os.environ.get(BinaryTargetVar, None)
    if not target or (target.lower() == BinaryTarget_Auto):
        install_handler()
    else:
        packaging_handler(target)


if __name__ == "__main__":
    main()
