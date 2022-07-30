#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import platform
import sysconfig
import setuptools
from os.path import (
    join,
    abspath,
    dirname,
    basename,
)

sys.path.insert(0, join(dirname(abspath(__file__)), "setupsrc"))
from pl_setup.packaging_base import (
    PlatformNames,
    SourceTree,
    SetupTargetVar,
)


def packaging_handler():
    
    target = os.environ.get(SetupTargetVar, None)
    if target in (None, "auto"):
        return True
    
    from pl_setup.setup_base import mkwheel, SetupKws
    
    if target == "sdist":
        setuptools.setup(**SetupKws)
    elif hasattr(PlatformNames, target):
        mkwheel( getattr(PlatformNames, target) )
    else:
        raise ValueError("Invalid deployment target '%s'" % target)
    
    return False


def install_handler():
    
    from pl_setup import check_deps
    
    def check_presetup():
        StatusFile = join(SourceTree, "data", ".presetup_done.txt")
        if os.path.exists(StatusFile):
            return False
        else:
            with open(StatusFile, "w") as fh:
                fh.write("")
            return True
    
    W_Presetup = check_presetup()
    if W_Presetup: check_deps.main()
    
    from pl_setup import update_pdfium  #, build_pdfium
    from pl_setup.setup_base import mkwheel
    
    class HostPlatform:
        
        def __init__(self):
            
            plat_name = sysconfig.get_platform().lower()
            for char in ("-", "."):
                plat_name = plat_name.replace(char, "_")
            self.plat_name = plat_name
            
            self.libc_name = None
            if self.plat_name.startswith("linux"):
                self.libc_name = platform.libc_ver()[0]
        
        def is_platform(self, start, end):
            if self.plat_name.startswith(start):
                if self.plat_name.endswith(end):
                    return True
            return False
        
        def is_libc(self, *libc_names):
            return any(self.libc_name == l for l in libc_names)
    
    def _setup(pl_name):
        if W_Presetup: update_pdfium.main( [basename(pl_name)] )
        mkwheel(pl_name)
    
    host = HostPlatform()
    
    if host.is_platform("macosx", "arm64"):
        _setup(PlatformNames.darwin_arm64)
    elif host.is_platform("macosx", "x86_64"):
        _setup(PlatformNames.darwin_x64)
    elif host.is_platform("linux", "armv7l"):
        _setup(PlatformNames.linux_arm32)
    elif host.is_platform("linux", "aarch64"):
        _setup(PlatformNames.linux_arm64)
    elif host.is_platform("linux", "x86_64") and host.is_libc("glibc"):
        _setup(PlatformNames.linux_x64)
    elif host.is_platform("linux", "i686") and host.is_libc("glibc"):
        _setup(PlatformNames.linux_x86)
    elif host.is_platform("linux", "x86_64") and host.is_libc("musl", ""):
        _setup(PlatformNames.musllinux_x64)
    elif host.is_platform("linux", "i686") and host.is_libc("musl", ""):
        _setup(PlatformNames.musllinux_x86)
    elif host.is_platform("win", "arm64"):
        _setup(PlatformNames.windows_arm64)
    elif host.is_platform("win", "amd64"):
        _setup(PlatformNames.windows_x64)
    elif host.is_platform("win32", ""):
        _setup(PlatformNames.windows_x86)
    else:
        raise RuntimeError("No pre-built binaries available for platform '%s' with libc implementation '%s'. You can attempt a source build, but it's unlikely to work out due to binary toolchain requirements of PDFium's build system. Doing cross-compilation or using a different build system might be possible, though. Please get in touch with the project maintainers." % (host.plat_name, host.libc_name))
        # if W_Presetup: build_pdfium.main()
        # mkwheel(PlatformNames.sourcebuild)


def main():
    cont = packaging_handler()
    if cont: install_handler()

if __name__ == "__main__":
    main()
