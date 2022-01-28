#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sysconfig
import update_pdfium
import build_pdfium
import setup_source
import setup_darwin_arm64
import setup_darwin_x64
import setup_linux_arm32
import setup_linux_arm64
import setup_linux_x64
import setup_windows_arm64
import setup_windows_x64
import setup_windows_x86
import _getdeps as getdeps
from os.path import join
from _packaging import DataTree


StatusFile = join(DataTree,'setup_status.txt')

def perform_presetup() -> bool:
    with open(StatusFile, 'r') as file_handle:
        content = file_handle.read().strip()
    if content == 'InitialState':
        return True
    elif content == 'PreSetupDone':
        return False
    else:
        raise ValueError( "Invalid content in setup status file: '{}'".format(content) )


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



def main():
    
    # Since setuptools may run this code multiple times with different commands,
    # we have a status file to check whether pre-setup tasks have already been done.
    # If you deliberately wish to re-run them, set the content of `data/setup_status.txt`
    # to `InitialState`.
    w_presetup = perform_presetup()
    
    
    # function to generate bindings, if doing pre-setup
    def _make_bindings(platform_str):
        if w_presetup: update_pdfium.main( ['-p', platform_str] )
    
    
    if w_presetup:
        
        # automatically check/install dependencies
        getdeps.main()
        
        # update staus file
        with open(StatusFile, 'w') as file_handle:
            file_handle.write("PreSetupDone")
    
    
    # tooling to determine the current platform
    plat = PlatformManager()
    
    # run the corresponding setup code
    if plat.is_darwin_arm64():
        _make_bindings('darwin-arm64')
        setup_darwin_arm64.main()
    
    elif plat.is_darwin_x64():
        _make_bindings('darwin-x64')
        setup_darwin_x64.main()
    
    elif plat.is_linux_arm32():
        _make_bindings('linux-arm32')
        setup_linux_arm32.main()
    
    elif plat.is_linux_arm64():
        _make_bindings('linux-arm64')
        setup_linux_arm64.main()
    
    elif plat.is_linux_x64():
        _make_bindings('linux-x64')
        setup_linux_x64.main()
    
    elif plat.is_windows_arm64():
        _make_bindings('windows-arm64')
        setup_windows_arm64.main()
    
    elif plat.is_windows_x64():
        _make_bindings('windows-x64')
        setup_windows_x64.main()
    
    elif plat.is_windows_x86():
        _make_bindings('windows-x86')
        setup_windows_x86.main()
    
    # Platform without pre-built binaries - trying a regular sourcebuild
    # In case it does not work, you may want to attempt a native build (`./build_pdfium -p`),
    # and then write a wheel to `dist/` using `python3 setup_source.py bdist_wheel`
    else:
        if w_presetup:
            args = build_pdfium.parse_args([])
            build_pdfium.main(args)
        setup_source.main()


if __name__ == '__main__':
    main()
