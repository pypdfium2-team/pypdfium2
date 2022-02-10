#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from os.path import join, basename
from platform_setup.packaging_base import DataTree


StatusFile = join(DataTree, 'setup_status.txt')

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
        file_handle.write("PreSetupDone")

W_Presetup = check_presetup()

if W_Presetup:
    from platform_setup import getdeps
    getdeps.main()


import sysconfig
from platform_setup.setup_base import PlatformDirs, wheel_for


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


def _setup(platform_dir):
    if W_Presetup:
        from platform_setup import update_pdfium
        update_pdfium.main( ['-p', basename(platform_dir)] )
    wheel_for(platform_dir)


def main():    
    
    plat = PlatformManager()
    
    if plat.is_darwin_arm64():
        _setup(PlatformDirs.DarwinArm64)
    elif plat.is_darwin_x64():
        _setup(PlatformDirs.Darwin64)
    elif plat.is_linux_arm32():
        _setup(PlatformDirs.LinuxArm32)
    elif plat.is_linux_arm64():
        _setup(PlatformDirs.LinuxArm64)
    elif plat.is_linux_x64():
        _setup(PlatformDirs.Linux64)
    elif plat.is_windows_arm64():
        _setup(PlatformDirs.WindowsArm64)
    elif plat.is_windows_x64():
        _setup(PlatformDirs.Windows64)
    elif plat.is_windows_x86():
        _setup(PlatformDirs.Windows86)
    else:
        # Platform without pre-built binaries - trying a regular sourcebuild
        if W_Presetup:
            from platform_setup import build_pdfium
            args = build_pdfium.parse_args([])
            build_pdfium.main(args)
        wheel_for(PlatformDirs.SourceBuild)
    
    presetup_done()


if __name__ == '__main__':
    main()
