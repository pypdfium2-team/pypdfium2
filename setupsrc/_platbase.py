# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import platform
import functools
import sysconfig
from pathlib import Path

if sys.version_info < (3, 8):
    # NOTE alternatively, we could write our own cached property backport with python's descriptor protocol
    def cached_property(func):
        return property( functools.lru_cache(maxsize=1)(func) )
else:
    cached_property = functools.cached_property


# TODO consider StrEnum or something

class SysNames:
    darwin  = "darwin"
    windows = "windows"
    linux   = "linux"
    android = "android"
    ios     = "ios"

class ExtPlats:
    sourcebuild = "sourcebuild"
    system      = "system"
    # `fallback` will resolve to either system-search or sourcebuild-native
    fallback    = "fallback"
    sdist       = "sdist"

class PlatNames:
    # - Attribute names and values are expected to match
    # - Platform names are expected to start with the corresponding system name
    darwin_x64       = SysNames.darwin  + "_x64"
    darwin_arm64     = SysNames.darwin  + "_arm64"
    darwin_univ2     = SysNames.darwin  + "_univ2"
    windows_x64      = SysNames.windows + "_x64"
    windows_x86      = SysNames.windows + "_x86"
    windows_arm64    = SysNames.windows + "_arm64"
    linux_x64        = SysNames.linux   + "_x64"
    linux_x86        = SysNames.linux   + "_x86"
    linux_arm64      = SysNames.linux   + "_arm64"
    linux_arm32      = SysNames.linux   + "_arm32"
    linux_musl_x64   = SysNames.linux   + "_musl_x64"
    linux_musl_x86   = SysNames.linux   + "_musl_x86"
    linux_musl_arm64 = SysNames.linux   + "_musl_arm64"
    android_arm64    = SysNames.android + "_arm64"       # device
    android_arm32    = SysNames.android + "_arm32"       # device
    android_x64      = SysNames.android + "_x64"         # emulator
    android_x86      = SysNames.android + "_x86"         # emulator
    ios_arm64_dev    = SysNames.ios     + "_arm64_dev"   # device
    ios_arm64_simu   = SysNames.ios     + "_arm64_simu"  # simulator
    ios_x64_simu     = SysNames.ios     + "_x64_simu"    # simulator


# Map platform names to the package names used by pdfium-binaries/google.
PdfiumBinariesMap = {
    PlatNames.darwin_x64:       "mac-x64",
    PlatNames.darwin_arm64:     "mac-arm64",
    PlatNames.windows_x64:      "win-x64",
    PlatNames.windows_x86:      "win-x86",
    PlatNames.windows_arm64:    "win-arm64",
    PlatNames.linux_x64:        "linux-x64",
    PlatNames.linux_x86:        "linux-x86",
    PlatNames.linux_arm64:      "linux-arm64",
    PlatNames.linux_arm32:      "linux-arm",
    PlatNames.linux_musl_x64:   "linux-musl-x64",
    PlatNames.linux_musl_x86:   "linux-musl-x86",
    PlatNames.linux_musl_arm64: "linux-musl-arm64",
}

# Capture the platforms we build wheels for
WheelPlatforms = list(PdfiumBinariesMap.keys())

# Additional platforms we don't currently build wheels for in craft.py
# To package these manually, you can do e.g. (in bash):
# export PLATFORMS=(darwin_univ2 android_arm64 android_arm32 android_x64 android_x86 ios_arm64_dev ios_arm64_simu ios_x64_simu)
# for PLAT in ${PLATFORMS[@]}; do echo $PLAT; just emplace $PLAT; PDFIUM_PLATFORM=$PLAT python3 -m build -wxn; done
PdfiumBinariesMap.update({
    PlatNames.darwin_univ2:   "mac-univ",
    PlatNames.android_arm64:  "android-arm64",
    PlatNames.android_arm32:  "android-arm",
    PlatNames.android_x64:    "android-x64",
    PlatNames.android_x86:    "android-x86",
    PlatNames.ios_arm64_dev:  "ios-device-arm64",
    PlatNames.ios_arm64_simu: "ios-simulator-arm64",
    PlatNames.ios_x64_simu:   "ios-simulator-x64",
})


def log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def libname_for_system(system, name="pdfium", prefix=None):
    # Map system to pdfium shared library name
    if prefix is None:
        prefix = "" if system == SysNames.windows else "lib"
    if system == SysNames.windows:
        return f"{prefix}{name}.dll"
    elif system in (SysNames.darwin, SysNames.ios):
        return f"{prefix}{name}.dylib"
    elif system in (SysNames.linux, SysNames.android):
        return f"{prefix}{name}.so"
    else:
        # take libname pattern from caller
        pattern = os.getenv("LIBNAME_PATTERN")
        if pattern:
            return pattern.format(name)
        # NOTE alternatively, we could do this only for BSD/POSIX
        # as a downstream fallback, we could also list the dir in question and pick the file that contains the libname
        log(f"Unhandled system {sys.platform!r}" + " - assuming 'lib{}.so' pattern. Set $LIBNAME_PATTERN if this is not right.")
        return f"lib{name}.so"


def plat_to_system(pl_name):
    if pl_name == ExtPlats.sourcebuild:
        # Note, this may be None if on an unknown host
        return Host.system
    # other ExtPlats intentionally not handled here
    return getattr(SysNames, pl_name.split("_", maxsplit=1)[0])


# platform.libc_ver() currently returns an empty string for musl, so use the packaging module to confirm.
# See https://github.com/python/cpython/issues/87414 and https://github.com/pypa/packaging/blob/f13c298f0a623f3f7e01cc8395956b718d21503a/src/packaging/_musllinux.py#L32
# (could consider packaging.tags.sys_tags() as a possible public-API alternative - see https://packaging.pypa.io/en/stable/tags.html#packaging.tags.sys_tags or https://stackoverflow.com/a/75172415/15547292)

def _get_libc_info():
    
    name, ver = platform.libc_ver()
    if name.startswith("musl"):
        # try to be future proof in case libc_ver() gets musl support but uses "muslc" rather than just "musl"
        name = "musl"
    elif name == "":
        import packaging._musllinux
        musl_ver = packaging._musllinux._get_musl_version(sys.executable)
        if musl_ver:
            name, ver = "musl", f"{musl_ver.major}.{musl_ver.minor}"
    
    return name.lower(), ver


def _android_api():
    try:
        # this is available since python 3.7 (i.e. earlier than PEP 738)
        return sys.getandroidapilevel()
    except AttributeError:
        return None


class _host_platform:
    
    def __init__(self):
        
        # Get info about the host platform (OS and CPU)
        # For the machine name, the platform module just passes through info provided by the OS (e.g. the uname command on unix), so we can determine the relevant names from Python's source code, system specs or info available online (e.g. https://en.wikipedia.org/wiki/Uname)
        self._raw_system = platform.system().lower()
        self._raw_machine = platform.machine().lower()
        
        if self._raw_system == "linux":
            self._libc_name, self._libc_ver = _get_libc_info()
        else:
            self._libc_name, self._libc_ver = "", ""
        
        self._exc = None
    
    @cached_property
    def platform(self):
        try:
            return self._get_platform()
        except Exception as e:
            self._exc = e
            return None
    
    @cached_property
    def system(self):
        have_platform = bool(self.platform)
        if have_platform:
            assert str(self.platform).startswith(f"{self._system}_"), f"'{self.platform}' does not start with '{self._system}_'"
        return self._system
    
    @cached_property
    def libname_glob(self):
        return libname_for_system(Host.system, name="*")
    
    # TODO convert to sysroot?
    @cached_property
    def usr(self):
        if os.name != "posix":
            return None
        usr = "/usr"
        if self.system == SysNames.android and os.getenv("TERMUX_VERSION"):
            # see https://github.com/termux/termux-packages/wiki/Termux-file-system-layout
            usr = os.getenv("PREFIX", "/data/data/com.termux/files/usr")
        return Path(usr)
    
    @cached_property
    def local_bin(self):
        # Path.home()/".local"/"bin"
        if sys.version_info >= (3, 10):
            user_scheme = sysconfig.get_preferred_scheme("user")
        elif os.name == "nt":
            user_scheme = "nt_user"
        elif sys.platform.startswith("darwin") and getattr(sys, "_framework", None):
            user_scheme = "osx_framework_user"
        else:
            user_scheme = "posix_user"
        return Path( sysconfig.get_path("scripts", scheme=user_scheme) )
    
    def __repr__(self):
        info = f"{self._raw_system} {self._raw_machine}"
        if self._raw_system == "linux" and self._libc_name:
            info += f", {self._libc_name} {self._libc_ver}"
        return f"<Host: {info}>"
    
    def _handle_linux(self, archid):
        if self._libc_name == "glibc":
            return getattr(PlatNames, f"linux_{archid}")
        elif self._libc_name == "musl":
            return getattr(PlatNames, f"linux_musl_{archid}")
        elif _android_api():  # seems to imply self._libc_name == "libc"
            log("Android prior to PEP 738 (e.g. Termux)")
            self._system = SysNames.android
            return getattr(PlatNames, f"android_{archid}")
        else:
            raise RuntimeError(f"Linux with unhandled libc {self._libc_name!r}")
    
    def _get_platform(self):
        
        # TODO 32-bit interpreters running on 64-bit machines?
        
        if self._raw_system == "darwin":
            # platform.machine() is the actual architecture. sysconfig.get_platform() may return universal2, but by default we only use the arch-specific binaries.
            self._system = SysNames.darwin
            log(f"macOS {self._raw_machine} {platform.mac_ver()}")
            if self._raw_machine == "x86_64":
                return PlatNames.darwin_x64
            elif self._raw_machine == "arm64":
                return PlatNames.darwin_arm64
            # see e.g. the table in https://github.com/pypa/packaging.python.org/pull/1804
            elif self._raw_machine in ("i386", "ppc", "ppc64"):
                raise RuntimeError(f"Unsupported legacy mac architecture: {self._raw_machine!r}")
        
        elif self._raw_system == "windows":
            self._system = SysNames.windows
            log(f"windows {self._raw_machine} {platform.win32_ver()}")
            if self._raw_machine == "amd64":
                return PlatNames.windows_x64
            elif self._raw_machine == "x86":
                return PlatNames.windows_x86
            elif self._raw_machine == "arm64":
                return PlatNames.windows_arm64
        
        elif self._raw_system == "linux":
            self._system = SysNames.linux
            log(f"linux {self._raw_machine} {self._libc_name, self._libc_ver}")
            if self._raw_machine == "x86_64":
                return self._handle_linux("x64")
            elif self._raw_machine == "i686":
                return self._handle_linux("x86")
            elif self._raw_machine == "aarch64":
                return self._handle_linux("arm64")
            elif self._raw_machine == "armv7l":
                if self._libc_name == "musl":
                    raise RuntimeError(f"armv7l: musl not supported at this time")
                return self._handle_linux("arm32")
        
        elif self._raw_system == "android":  # PEP 738
            # The PEP isn't too explicit about the machine names, but based on related CPython PRs, it looks like platform.machine() retains the raw uname values as on Linux, whereas sysconfig.get_platform() will map to the wheel tags
            self._system = SysNames.android
            log(f"android {self._raw_machine} {sys.getandroidapilevel()} {platform.android_ver()}")
            if self._raw_machine == "aarch64":
                return PlatNames.android_arm64
            elif self._raw_machine == "armv7l":
                return PlatNames.android_arm32
            elif self._raw_machine == "x86_64":
                return PlatNames.android_x64
            elif self._raw_machine == "i686":
                return PlatNames.android_x86
        
        elif self._raw_system in ("ios", "ipados"):  # PEP 730
            # This is currently untested. We don't have access to an iOS device, so this is basically guessed from what the PEP mentions.
            self._system = SysNames.ios
            ios_ver = platform.ios_ver()
            log(f"{self._raw_system} {self._raw_machine} {ios_ver}")
            if self._raw_machine == "arm64":
                return PlatNames.ios_arm64_simu if ios_ver.is_simulator else PlatNames.ios_arm64_dev
            elif self._raw_machine == "x86_64":
                assert ios_ver.is_simulator, "iOS x86_64 can only be simulator"
                return PlatNames.ios_x64_simu
        
        else:
            self._system = None
        
        raise RuntimeError(f"Unhandled platform: {self!r}")

Host = _host_platform()


def _manylinux_tag(arch, glibc="2_17"):
    # see BUG(203) for discussion of glibc requirement
    return f"manylinux_{glibc}_{arch}.manylinux2014_{arch}"

def get_wheel_tag(pl_name):
    
    if pl_name == PlatNames.darwin_x64:
        # AOTW, pdfium-binaries/steps/05-configure.sh defines mac_deployment_target = "11.0.0"
        return "macosx_11_0_x86_64"
    elif pl_name == PlatNames.darwin_arm64:
        # macOS 11 is the first version available on arm64
        return "macosx_11_0_arm64"
    elif pl_name == PlatNames.darwin_univ2:
        # universal binary format (combo of x64 and arm64) - we prefer arch-specific wheels, but allow callers to build a universal wheel if they want to
        return "macosx_11_0_universal2"
    
    elif pl_name == PlatNames.windows_x64:
        return "win_amd64"
    elif pl_name == PlatNames.windows_arm64:
        return "win_arm64"
    elif pl_name == PlatNames.windows_x86:
        return "win32"
    
    elif pl_name == PlatNames.linux_x64:
        return _manylinux_tag("x86_64")
    elif pl_name == PlatNames.linux_x86:
        return _manylinux_tag("i686")
    elif pl_name == PlatNames.linux_arm64:
        return _manylinux_tag("aarch64")
    elif pl_name == PlatNames.linux_arm32:
        return _manylinux_tag("armv7l")
    
    # pdfium-binaries statically link musl, so we can declare the lowest possible requirement.
    # The builds have been confirmed to work in a musllinux_1_1 container, as of Nov 2025.
    elif pl_name == PlatNames.linux_musl_x64:
        return "musllinux_1_1_x86_64"
    elif pl_name == PlatNames.linux_musl_x86:
        return "musllinux_1_1_i686"
    elif pl_name == PlatNames.linux_musl_arm64:
        return "musllinux_1_1_aarch64"
    
    # Android - see PEP 738 # Packaging
    # We don't currently publish wheels for Android, but handle it in case we want to in the future (or if callers want to build their own wheels)
    # AOTW, pdfium-binaries/steps/05-configure.sh defines default_min_sdk_version = 23
    elif pl_name == PlatNames.android_arm64:
        return "android_23_arm64_v8a"
    elif pl_name == PlatNames.android_arm32:
        return "android_23_armeabi_v7a"
    elif pl_name == PlatNames.android_x64:
        return "android_23_x86_64"
    elif pl_name == PlatNames.android_x86:
        return "android_23_x86"
    
    # iOS - see PEP 730 # Packaging
    # We do not currently build wheels for iOS, but again, add the handlers so it could be done on demand. Bear in mind that the resulting iOS packages are currently completely untested. In particular, the PEP says
    # "These wheels can include binary modules in-situ (i.e., co-located with the Python source, in the same way as wheels for a desktop platform); however, they will need to be post-processed as binary modules need to be moved into the “Frameworks” location for distribution. This can be automated with an Xcode build step."
    # I take it this means you may need to change the library search path to that Frameworks location.
    elif pl_name == PlatNames.ios_arm64_dev:
        return "ios_12_0_arm64_iphoneos"
    elif pl_name == PlatNames.ios_arm64_simu:
        return "ios_12_0_arm64_iphonesimulator"
    elif pl_name == PlatNames.ios_x64_simu:
        return "ios_12_0_x86_64_iphonesimulator"
    
    # The sourcebuild clause is currently inactive; setup.py will simply forward the tag determined by bdist_wheel. Anyway, this should be roughly equivalent.
    elif pl_name == ExtPlats.sourcebuild:
        tag = sysconfig.get_platform().replace("-", "_").replace(".", "_")
        # sysconfig.get_platform() may return universal2 on macOS. However, the binaries built here should be considered architecture-specific.
        if tag.startswith("macosx") and tag.endswith("universal2"):
            tag = tag[:-len("universal2")] + Host._raw_machine
        return tag
    
    else:
        raise ValueError(f"Unhandled platform name {pl_name}") 
