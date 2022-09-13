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
)

sys.path.insert(0, join(dirname(abspath(__file__)), "setupsrc"))
from pl_setup import check_deps
from pl_setup.packaging_base import (
    HostPlatform,
    PlatformNames,
    SourceTree,
    BinaryTargetVar,
    BinaryTarget_None,
)


# TODO(#136@geisserml) Replace with separate version status files per platform.

StatusFile = join(SourceTree, "data", ".presetup_done.txt")

def check_presetup():
    if os.path.exists(StatusFile):
        return False
    else:
        with open(StatusFile, "w") as fh:
            fh.write("")
        return True


def install_handler(w_presetup):
    
    from pl_setup import update_pdfium
    from pl_setup.setup_base import mkwheel
    
    host = HostPlatform()
    pl_name = host.get_name()
    
    if pl_name is None:
        # If PDFium had a proper build system, we could trigger a source build here
        raise RuntimeError(
            "No pre-built binaries available for platform '%s' with libc implementation '%s'. " % (host.plat_info, host.libc_info) +
            "You can attempt a source build, but it's unlikely to work out due to binary toolchain requirements of PDFium's build system. Doing cross-compilation or using a different build system might be possible, though. Please get in touch with the project maintainers."
        )
    
    if w_presetup:
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
        w_presetup = check_presetup()
        if w_presetup:
            check_deps.main()
        install_handler(w_presetup)
    else:
        packaging_handler(target)


if __name__ == "__main__":
    main()
