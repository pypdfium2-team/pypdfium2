# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from base import *  # local

def _manylinux_tag(arch):
    return "manylinux_{}" + f"_{arch}" + f".manylinux2014_{arch}"  # see below

_WheeltagPatterns = {
    # -- MINVER info is provided on an "AS OF THIS WRITING" basis (06/2026) --
    
    # MINVER(macOS): Can be checked with `vtool` (requires a macOS host). Upstream no longer specify a deployment target in config.
    PlatNames.darwin_x64:       ("macosx_{}_x86_64", "12_0"),
    PlatNames.darwin_arm64:     ("macosx_{}_arm64",  "12_0"),
    # universal binary format (combo of x64 and arm64) - we prefer arch-specific wheels, but allow callers to build a universal wheel if they want to
    PlatNames.darwin_univ2:     ("macosx_{}_universal2", "12_0"),
    
    # MINVER(windows): Windows tags are not versioned. FWIW, the minimum Windows version might be 7 or 8.
    PlatNames.windows_x64:      ("win_amd64", None),
    PlatNames.windows_arm64:    ("win_arm64", None),
    PlatNames.windows_x86:      ("win32",     None),
    
    # MINVER(linux-glibc): Can be checked with `auditwheel show`. Upstream build system uses sysroots with symbol reversioning, hence consistently low glibc requirement. Need to watch out for changes, though.
    PlatNames.linux_x64:        (_manylinux_tag("x86_64"),  "2_17"),
    PlatNames.linux_x86:        (_manylinux_tag("i686"),    "2_17"),
    PlatNames.linux_arm64:      (_manylinux_tag("aarch64"), "2_17"),
    PlatNames.linux_arm32:      (_manylinux_tag("armv7l"),  "2_17"),
    PlatNames.linux_ppc64le:    (_manylinux_tag("ppc64le"), "2_17"),
    
    # MINVER(linux-musl): pdfium-binaries statically link musl, so we can declare the lowest possible requirement. The builds have been confirmed to work in a musllinux_1_1 container, as of Nov 2025.
    PlatNames.linux_musl_x64:   ("musllinux_{}_x86_64",  "1_1"),
    PlatNames.linux_musl_x86:   ("musllinux_{}_i686",    "1_1"),
    PlatNames.linux_musl_arm64: ("musllinux_{}_aarch64", "1_1"),
    
    # Android - see PEP 738 # Packaging
    # MINVER(android): pdfium-binaries/steps/05-configure.sh says default_min_sdk_version = 23
    PlatNames.android_arm64:    ("android_{}_arm64_v8a",   "23"),
    PlatNames.android_arm32:    ("android_{}_armeabi_v7a", "23"),
    PlatNames.android_x64:      ("android_{}_x86_64",      "23"),
    PlatNames.android_x86:      ("android_{}_x86",         "23"),
    
    # iOS - see PEP 730 # Packaging
    # We do not currently build wheels for iOS, but again, add the handlers so it could be done on demand. Untested. Note that the PEP says:
    # "These wheels can include binary modules in-situ (i.e., co-located with the Python source, in the same way as wheels for a desktop platform); however, they will need to be post-processed as binary modules need to be moved into the “Frameworks” location for distribution. This can be automated with an Xcode build step."
    # I take it this means you'd need to change the library search path to that Frameworks location in bindings.
    # MINVER(ios): Unclear, guessed from the lowest version XCode 26 can achieve according to [1]
    # [1]: https://developer.apple.com/xcode/system-requirements/
    PlatNames.ios_arm64_dev:    ("ios_{}_arm64_iphoneos",         "15_0"),
    PlatNames.ios_arm64_simu:   ("ios_{}_arm64_iphonesimulator",  "15_0"),
    PlatNames.ios_x64_simu:     ("ios_{}_x86_64_iphonesimulator", "15_0"),
}

def get_wheel_tag(pl_name, dll_path):
    tag_pattern, hardcoded_version = _WheeltagPatterns[pl_name]
    return tag_pattern.format(hardcoded_version)
