#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import sysconfig
import setuptools
import importlib.util
from os.path import (
    join,
    abspath,
    dirname,
    basename,
)


def include_platform_setup():
    
    mod_name = 'platform_setup'
    PlatSetupInit = join(dirname(abspath(__file__)), mod_name, '__init__.py')
    
    spec = importlib.util.spec_from_file_location(mod_name, PlatSetupInit)
    sys.modules[mod_name] = importlib.util.module_from_spec(spec)


def packaging_handler():    
    
    target = os.environ.get('PYP_TARGET_PLATFORM', None)
    if target in (None, 'auto'):
        return True
    
    from platform_setup.setup_base import mkwheel, SetupKws
    from platform_setup.packaging_base import PlatformNames
    
    if target == 'sdist':
        setuptools.setup(**SetupKws)
    elif hasattr(PlatformNames, target):
        mkwheel( getattr(PlatformNames, target) )
    else:
        raise ValueError( "Invalid deployment target '{}'".format(target) )
    
    return False


def install_handler():
    
    from platform_setup import check_deps
    from platform_setup.packaging_base import SourceTree, PlatformNames
    
    
    StatusFile = join(SourceTree, 'platform_setup', 'setup_status.txt')
    
    def check_presetup() -> bool:
        with open(StatusFile, 'r') as file_handle:
            content = file_handle.read().strip()
        if content == 'InitialState':
            return True
        elif content == 'PreSetupDone':
            return False
        else:
            raise ValueError( "Invalid content in setup status file: '{}'".format(content) )
    
    def presetup_done():
        with open(StatusFile, 'w') as file_handle:
            file_handle.write('PreSetupDone')
    
    W_Presetup = check_presetup()
    if W_Presetup:
        check_deps.main()
    
    
    from platform_setup import build_pdfium, update_pdfium
    from platform_setup.setup_base import mkwheel
    
    
    class PlatformManager:
        
        def __init__(self):
            
            plat_name = sysconfig.get_platform().lower()
            for char in ('-', '.'):
                plat_name = plat_name.replace(char, '_')
            
            self.plat_name = plat_name
        
        def _is_platform(self, start, end):
            if self.plat_name.startswith(start):
                if self.plat_name.endswith(end):
                    return True
            return False
        
        def is_darwin_arm64(self):
            return self._is_platform('macosx', 'arm64')
        def is_darwin_x64(self):
            return self._is_platform('macosx', 'x86_64')
        def is_linux_arm32(self):
            return self._is_platform('linux', 'armv7l')
        def is_linux_arm64(self):
            return self._is_platform('linux', 'aarch64')
        def is_linux_x64(self):
            return self._is_platform('linux', 'x86_64')
        def is_windows_arm64(self):
            return self._is_platform('win', 'arm64')    
        def is_windows_x64(self):
            return self._is_platform('win', 'amd64')
        def is_windows_x86(self):
            return self._is_platform('win32', '')
    
    
    def _setup(pl_name):
        if W_Presetup:
            update_pdfium.main( [basename(pl_name)] )
        mkwheel(pl_name)
    
    
    plat = PlatformManager()
    
    if plat.is_darwin_arm64():
        _setup(PlatformNames.darwin_arm64)
    elif plat.is_darwin_x64():
        _setup(PlatformNames.darwin_x64)
    elif plat.is_linux_arm32():
        _setup(PlatformNames.linux_arm32)
    elif plat.is_linux_arm64():
        _setup(PlatformNames.linux_arm64)
    elif plat.is_linux_x64():
        _setup(PlatformNames.linux_x64)
    elif plat.is_windows_arm64():
        _setup(PlatformNames.windows_arm64)
    elif plat.is_windows_x64():
        _setup(PlatformNames.windows_x64)
    elif plat.is_windows_x86():
        _setup(PlatformNames.windows_x86)
    else:
        # Platform without pre-built binaries - try a regular sourcebuild
        if W_Presetup:
            build_pdfium.main()
        mkwheel(PlatformNames.sourcebuild)
    
    presetup_done()


def main():
    include_platform_setup()
    cont = packaging_handler()
    if cont:
        install_handler()


if __name__ == '__main__':
    main()
