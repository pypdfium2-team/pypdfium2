# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import functools
from importlib.util import find_spec
from base import *  # local


def _manylinux_tag(arch):
    return "manylinux_{}" + f"_{arch}" + f".manylinux2014_{arch}"  # see below

_WheeltagPatterns = {
    # -- Minver info is provided on an "AS OF THIS WRITING" basis (06/2026) --
    
    # Minver can be checked with `vtool` on a native host, or (cross-)checked with macholib. Upstream no longer specify a deployment target in config.
    PlatNames.darwin_x64:       ("macosx_{}_x86_64", "12_0"),
    PlatNames.darwin_arm64:     ("macosx_{}_arm64",  "12_0"),
    # universal binary format (combo of x64 and arm64) - we prefer arch-specific wheels, but allow callers to build a universal wheel if they want to
    PlatNames.darwin_univ2:     ("macosx_{}_universal2", "12_0"),
    
    # Windows tags are not versioned. FWIW, the minimum Windows version might be 7 or 8.
    PlatNames.windows_x64:      ("win_amd64", None),
    PlatNames.windows_arm64:    ("win_arm64", None),
    PlatNames.windows_x86:      ("win32",     None),
    
    # Minver can be checked with `auditwheel show`. Upstream build system uses sysroots with symbol reversioning, hence consistently low glibc requirement. Need to watch out for changes, though.
    PlatNames.linux_x64:        (_manylinux_tag("x86_64"),  "2_17"),
    PlatNames.linux_x86:        (_manylinux_tag("i686"),    "2_17"),
    PlatNames.linux_arm64:      (_manylinux_tag("aarch64"), "2_17"),
    PlatNames.linux_arm32:      (_manylinux_tag("armv7l"),  "2_17"),
    PlatNames.linux_ppc64le:    (_manylinux_tag("ppc64le"), "2_17"),
    
    # pdfium-binaries statically link musl, so we can declare the lowest possible requirement. The builds have been confirmed to work in a musllinux_1_1 container, as of Nov 2025.
    PlatNames.linux_musl_x64:   ("musllinux_{}_x86_64",  "1_1"),
    PlatNames.linux_musl_x86:   ("musllinux_{}_i686",    "1_1"),
    PlatNames.linux_musl_arm64: ("musllinux_{}_aarch64", "1_1"),
    
    # Android - see PEP 738 # Packaging
    # pdfium-binaries/steps/05-configure.sh says default_min_sdk_version = 23
    PlatNames.android_arm64:    ("android_{}_arm64_v8a",   "23"),
    PlatNames.android_arm32:    ("android_{}_armeabi_v7a", "23"),
    PlatNames.android_x64:      ("android_{}_x86_64",      "23"),
    PlatNames.android_x86:      ("android_{}_x86",         "23"),
    
    # iOS - see PEP 730 # Packaging
    # We do not currently build wheels for iOS, but again, add the handlers so it could be done on demand. Untested. Note that the PEP says:
    # "These wheels can include binary modules in-situ (i.e., co-located with the Python source, in the same way as wheels for a desktop platform); however, they will need to be post-processed as binary modules need to be moved into the “Frameworks” location for distribution. This can be automated with an Xcode build step."
    # I take it this means you'd need to change the library search path to that Frameworks location in bindings.
    # Minver can be (cross-)checked with `macholib`.
    PlatNames.ios_arm64_dev:    ("ios_{}_arm64_iphoneos",         "26_0"),
    PlatNames.ios_arm64_simu:   ("ios_{}_arm64_iphonesimulator",  "26_0"),
    PlatNames.ios_x64_simu:     ("ios_{}_x86_64_iphonesimulator", "26_0"),
}


HAVE_MACHOLIB = bool(find_spec("macholib"))
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


def autominver(dll_path, sys_name, hardcoded_ver):
    
    autotag_ok = bool(int( os.environ.get("AUTOTAG_OK", 1) ))
    if not autotag_ok:
        return None
    
    # TODO implement auto-versioning for other OSes
    detected_ver = None
    if sys_name in (SysNames.darwin, SysNames.ios) and HAVE_MACHOLIB:
        mac_major, mac_minor = mac_get_version(dll_path)
        log(f"Auto-detected min macOS version for {dll_path.name}: {mac_major, mac_minor}")
        detected_ver = f"{mac_major}_{mac_minor}"
    
    if detected_ver and (detected_ver != hardcoded_ver):
        log(f"Warning: detected {detected_ver!r} != hardcoded {hardcoded_ver!r}. Probably the hardcoded version is outdated, or the detected version might be incorrect.")
    
    return detected_ver


@functools.lru_cache(maxsize=1)
def get_wheel_tag(pl_name, dll_path):
    sys_name = plat_to_system(pl_name)
    tag_pattern, hardcoded_ver = _WheeltagPatterns[pl_name]
    detected_ver = autominver(dll_path, sys_name, hardcoded_ver)
    return tag_pattern.format(detected_ver or hardcoded_ver)
