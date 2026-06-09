# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
from importlib.util import find_spec

from base import *  # local


def _manylinux_tag(arch):
    return "manylinux_{}" + f"_{arch}" + f".manylinux2014_{arch}"  # see below

_WheeltagPatterns = {
    PlatNames.darwin_x64:       "macosx_{}_x86_64",
    PlatNames.darwin_arm64:     "macosx_{}_arm64",
    # universal binary format (combo of x64 and arm64) - we prefer arch-specific wheels, but allow callers to build a universal wheel if they want to
    PlatNames.darwin_univ2:     "macosx_{}_universal2",
    
    PlatNames.windows_x64:      "win_amd64",
    PlatNames.windows_arm64:    "win_arm64",
    PlatNames.windows_x86:      "win32",
    
    PlatNames.linux_x64:        _manylinux_tag("x86_64"),
    PlatNames.linux_x86:        _manylinux_tag("i686"),
    PlatNames.linux_arm64:      _manylinux_tag("aarch64"),
    PlatNames.linux_arm32:      _manylinux_tag("armv7l"),
    PlatNames.linux_ppc64le:    _manylinux_tag("ppc64le"),
    
    PlatNames.linux_musl_x64:   "musllinux_{}_x86_64",
    PlatNames.linux_musl_x86:   "musllinux_{}_i686",
    PlatNames.linux_musl_arm64: "musllinux_{}_aarch64",
    
    # Android - see PEP 738 # Packaging
    PlatNames.android_arm64:    "android_{}_arm64_v8a",
    PlatNames.android_arm32:    "android_{}_armeabi_v7a",
    PlatNames.android_x64:      "android_{}_x86_64",
    PlatNames.android_x86:      "android_{}_x86",
    
    # iOS - see PEP 730 # Packaging
    # We do not currently build wheels for iOS, but again, add the handlers so it could be done on demand. Untested. Note that the PEP says:
    # "These wheels can include binary modules in-situ (i.e., co-located with the Python source, in the same way as wheels for a desktop platform); however, they will need to be post-processed as binary modules need to be moved into the “Frameworks” location for distribution. This can be automated with an Xcode build step."
    # I take it this means you'd need to change the library search path to that Frameworks location in bindings.
    PlatNames.ios_arm64_dev:    "ios_{}_arm64_iphoneos",
    PlatNames.ios_arm64_simu:   "ios_{}_arm64_iphonesimulator",
    PlatNames.ios_x64_simu:     "ios_{}_x86_64_iphonesimulator",
}

_WheeltagVersions = {
    # --- AS OF THIS WRITING ---
    
    # macOS: Upstream does not specify a deployment target in config. Can be checked with our auto-tagging codepath (requires a macOS host).
    SysNames.darwin: "12_0",
    
    # iOS: unclear, guessed from the lowest version XCode 26 can achieve according to [1]
    # [1]: https://developer.apple.com/xcode/system-requirements/
    SysNames.ios: "15_0",
    
    # Linux (glibc): Upstream does not state the version. Build system uses sysroots with symbol reversioning, hence consistently low glibc requirement. Need to watch out for upstream changes, though. Can be checked with `auditwheel show`.
    SysNames.linux: "2_17",
    
    # Linux (musl): pdfium-binaries statically link musl, so we can declare the lowest possible requirement. The builds have been confirmed to work in a musllinux_1_1 container, as of Nov 2025.
    SysNames.linux_musl: "1_1",
    
    # pdfium-binaries/steps/05-configure.sh says default_min_sdk_version = 23
    SysNames.android: "23",
    
    # Windows tags are not versioned, .format() will ignore this
    SysNames.windows: None,
}


HAVE_MACHOLIB = sys.platform.startswith("darwin") and bool(find_spec("macholib"))
if HAVE_MACHOLIB:
    from macholib.MachO import MachO
    from macholib.mach_o import LC_BUILD_VERSION, LC_VERSION_MIN_MACOSX  # CPU_TYPE_NAMES

def _mac_iter_versions(dll_path):
    # adapted from matthew-brett/delocate
    macho = MachO(dll_path)
    for header in macho.headers:
        for cmd in header.commands:
            if cmd[0].cmd == LC_BUILD_VERSION:
                raw_version = cmd[1].minos
            elif cmd[0].cmd == LC_VERSION_MIN_MACOSX:
                raw_version = cmd[1].version
            else:
                continue
            # cpu_type = CPU_TYPE_NAMES.get(header.header.cputype, "unknown")
            yield (raw_version >> 16 & 0xFF), (raw_version >> 8 & 0xFF)
            break

def mac_get_version(dll_path):
    return max(_mac_iter_versions(dll_path))


def get_wheel_tag(pl_name, dll_path, autotag):
    
    tag_pattern = _WheeltagPatterns[pl_name]
    if autotag:
        if sys.platform.startswith("darwin") and HAVE_MACHOLIB:
            mac_major, mac_minor = mac_get_version(dll_path)
            log(f"Auto-detected min macOS version for {dll_path.name}: {mac_major, mac_minor}")
            return tag_pattern.format(f"{mac_major}_{mac_minor}")
        else:
            log("Auto-tagging unavailable, falling back to static tag.")
    
    sys_name = plat_to_system(pl_name, distinguish_musl=True)
    hardcoded_version = _WheeltagVersions[sys_name]
    return tag_pattern.format(hardcoded_version)
