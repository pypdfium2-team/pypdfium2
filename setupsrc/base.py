# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import re
import sys
import json
import stat
import shutil
import tarfile
import platform
import argparse
import functools
import sysconfig
import subprocess
import contextlib
from pathlib import Path
from collections import namedtuple
import urllib.request as url_request

if sys.version_info < (3, 8):
    # NOTE alternatively, we could write our own cached property backport with python's descriptor protocol
    def cached_property(func):
        return property( functools.lru_cache(maxsize=1)(func) )
else:
    cached_property = functools.cached_property

if sys.version_info < (3, 8):
    class ExtendAction (argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            items = getattr(namespace, self.dest) or []
            items.extend(values)
            setattr(namespace, self.dest, items)
else:
    ExtendAction = None

PDFIUM_MIN_REQ = 6635

# The PDFium versions our build scripts have last been tested with. Ideally, they should be close to the release version in autorelease/record.json
# To bump these versions, first test locally and update any patches as needed. Then, make a branch and run "Test Sourcebuild" on CI to see if all targets continue to work. Commit the new version to the main branch only when all is green. Better stay on an older version for a while than break a target.
# Updating and testing the patch sets can be a lot of work, so we might not want to do this too frequrently.
SBUILD_NATIVE_PIN = 7191
SBUILD_TOOLCHAINED_PIN = 7191

PlatSpec_EnvVar = "PDFIUM_PLATFORM"
PlatSpec_VerSep = ":"
PlatSpec_V8Sym  = "-v8"

BindSpec_EnvVar = "PDFIUM_BINDINGS"
IS_CI = bool(os.getenv("GITHUB_ACTIONS")) or bool(int(os.getenv("CIBUILDWHEEL", 0)))
USE_REFBINDINGS = os.getenv(BindSpec_EnvVar) == "reference" or not any((shutil.which("ctypesgen"), IS_CI))

ModulesSpec_EnvVar = "PYPDFIUM_MODULES"
ModuleRaw          = "raw"
ModuleHelpers      = "helpers"
ModulesAll         = (ModuleRaw, ModuleHelpers)

BindingsFN = "bindings.py"
VersionFN  = "version.json"

ProjectDir        = Path(__file__).parents[1].resolve()
DataDir           = ProjectDir / "data"
DataDir_Bindings  = DataDir / "bindings"
BindingsFile      = DataDir_Bindings / BindingsFN
PatchDir          = ProjectDir / "patches"
ModuleDir_Raw     = ProjectDir / "src" / "pypdfium2_raw"
ModuleDir_Helpers = ProjectDir / "src" / "pypdfium2"
Changelog         = ProjectDir / "docs" / "devel" / "changelog.md"
ChangelogStaging  = ProjectDir / "docs" / "devel" / "changelog_staging.md"

AutoreleaseDir  = ProjectDir / "autorelease"
AR_RecordFile   = AutoreleaseDir / "record.json"
AR_ConfigFile   = AutoreleaseDir / "config.json"
RefBindingsFile = AutoreleaseDir / BindingsFN

RepositoryURL  = "https://github.com/pypdfium2-team/pypdfium2"
PdfiumURL      = "https://pdfium.googlesource.com/pdfium"
DepotToolsURL  = "https://chromium.googlesource.com/chromium/tools/depot_tools.git"
ReleaseRepo    = "https://github.com/bblanchon/pdfium-binaries"
ReleaseURL     = ReleaseRepo + "/releases/download/chromium%2F"
ReleaseInfoURL = ReleaseURL.replace("github.com/", "api.github.com/repos/").replace("download/", "tags/")

LIBNAME_GLOBS = ("lib*.so", "lib*.dylib", "*.dll")
REFBINDINGS_FLAGS = ("V8", "XFA", "SKIA")

PdfiumFlagsDict = {
    "V8": "PDF_ENABLE_V8",
    "XFA": "PDF_ENABLE_XFA",
    "SKIA": "PDF_USE_SKIA",
}


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
    linux_ppc64le    = SysNames.linux   + "_ppc64le"
    linux_musl_x64   = SysNames.linux   + "_musl_x64"
    linux_musl_x86   = SysNames.linux   + "_musl_x86"
    linux_musl_arm64 = SysNames.linux   + "_musl_arm64"
    android_arm64    = SysNames.android + "_arm64"       # device
    android_arm32    = SysNames.android + "_arm32"       # device
    android_x64      = SysNames.android + "_x64"         # simulator
    android_x86      = SysNames.android + "_x86"         # simulator
    ios_arm64_dev    = SysNames.ios     + "_arm64_dev"   # device
    ios_arm64_simu   = SysNames.ios     + "_arm64_simu"  # simulator
    ios_x64_simu     = SysNames.ios     + "_x64_simu"    # simulator

# Map platform names to the package names used by pdfium-binaries/google.
PdfiumBinariesMap = {
    PlatNames.darwin_x64:    "mac-x64",
    PlatNames.darwin_arm64:  "mac-arm64",
    PlatNames.windows_x64:   "win-x64",
    PlatNames.windows_x86:   "win-x86",
    PlatNames.windows_arm64: "win-arm64",
    PlatNames.linux_x64:     "linux-x64",
    PlatNames.linux_x86:     "linux-x86",
    PlatNames.linux_arm64:   "linux-arm64",
    PlatNames.linux_arm32:   "linux-arm",
    PlatNames.linux_ppc64le: "linux-ppc64",
    PlatNames.android_arm64: "android-arm64",
    PlatNames.android_arm32: "android-arm",
}

# Capture the platforms we build wheels for
WheelPlatforms = list(PdfiumBinariesMap.keys())

# Additional platforms we don't currently build wheels for this way in craft.py
# To package these manually, you can do e.g. (in bash):
# export PLATFORMS=(linux_musl_x64 linux_musl_x86 linux_musl_arm64 darwin_univ2 android_x64 android_x86 ios_arm64_dev ios_arm64_simu ios_x64_simu)
# for PLAT in ${PLATFORMS[@]}; do echo $PLAT; just emplace $PLAT; PDFIUM_PLATFORM=$PLAT python3 -m build -wxn; done
PdfiumBinariesMap.update({
    PlatNames.linux_musl_x64:   "linux-musl-x64",
    PlatNames.linux_musl_x86:   "linux-musl-x86",
    PlatNames.linux_musl_arm64: "linux-musl-arm64",
    PlatNames.darwin_univ2:     "mac-univ",
    PlatNames.android_x64:      "android-x64",
    PlatNames.android_x86:      "android-x86",
    PlatNames.ios_arm64_dev:    "ios-device-arm64",
    PlatNames.ios_arm64_simu:   "ios-simulator-arm64",
    PlatNames.ios_x64_simu:     "ios-simulator-x64",
})


def log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

def mkdir(path, exist_ok=True, parents=True):
    path.mkdir(exist_ok=exist_ok, parents=parents)

def read_json(fp):
    with open(fp, "r") as buf:
        return json.load(buf)

def write_json(fp, data, indent=2):
    with open(fp, "w") as buf:
        return json.dump(data, buf, indent=indent)


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


IGNORE_FULLVER = bool(int(os.environ.get("IGNORE_FULLVER", 0)))
GIVEN_FULLVER = os.environ.get("GIVEN_FULLVER")

class _PdfiumVerScheme (
    namedtuple("PdfiumVerScheme", ("major", "minor", "build", "patch"))
):
    def __str__(self):
        return ".".join(str(n) for n in self)

class _PdfiumVerClass:
    
    scheme = _PdfiumVerScheme
    
    def __init__(self):
        self._vlines = None
    
    @cached_property
    def _vdict(self):
        if GIVEN_FULLVER:
            log("Warning: taking full versions from caller via $GIVEN_FULLVER (could be incorrect)")
            version_strs = GIVEN_FULLVER.split(":")
            versions = (self.scheme(*(int(n) for n in ver.split("."))) for ver in version_strs)
            return {v.build: v for v in versions}
        else:
            return {}
    
    @staticmethod
    @functools.lru_cache(maxsize=1)
    def get_latest():
        "Returns the latest release version of pdfium-binaries."
        git_ls = run_cmd(["git", "ls-remote", f"{ReleaseRepo}.git"], cwd=None, capture=True)
        tag = git_ls.split("\t")[-1]
        return int( tag.split("/")[-1] )
    
    @functools.lru_cache(maxsize=1)
    def _get_chromium_refs(self):
        # FIXME The ls-remote call may take extremely long (~1min) with older versions of git!
        # With newer git, it's a lot better, but still noticeable (one or a few seconds).
        if self._vlines is None:
            log(f"Attempting to fetch chromium refs. If this causes setup to halt, set e.g. IGNORE_FULLVER=1")
            ChromiumURL = "https://chromium.googlesource.com/chromium/src"
            self._vlines = run_cmd(["git", "ls-remote", "--sort", "-version:refname", "--tags", f"{ChromiumURL}.git", '*.*.*.0'], cwd=None, capture=True).split("\n")
        return self._vlines
    
    def _parse_line(self, line):
        ref = line.split("\t")[-1].rsplit("/", maxsplit=1)[-1]
        full_ver = self.scheme(*[int(v) for v in ref.split(".")])
        self._vdict[full_ver.build] = full_ver
        return full_ver
    
    def get_latest_upstream(self):
        "Returns the latest version of upstream pdfium/chromium."
        lines = self._get_chromium_refs()
        full_ver = self._parse_line( lines.pop(0) )
        return full_ver
    
    if IGNORE_FULLVER:
        assert not IS_CI and not GIVEN_FULLVER
        def to_full(self, v_short):
            log(f"Warning: Full version ignored as per $IGNORE_FULLVER setting - will use NaN placeholders for {v_short}.")
            return self.scheme(NaN, NaN, v_short, NaN)
        
    else:
        def to_full(self, v_short):
            "Converts a build number to a full version."
            v_short = int(v_short)
            if v_short not in self._vdict:
                self._get_chromium_refs()
                for i, line in enumerate(self._vlines):
                    full_ver = self._parse_line(line)
                    if full_ver.build == v_short:
                        self._vlines = self._vlines[i+1:]
                        break
            full_ver = self._vdict[v_short]
            log(f"Resolved {v_short} -> {full_ver}")
            return full_ver
    
    @cached_property
    def pinned(self):
        # comments are not permitted in JSON, so the reason for the post_pdfium pin (if set) goes here:
        # (not currently pinned)
        record = read_json(AR_RecordFile)
        return record["post_pdfium"] or record["pdfium"]

PdfiumVer = _PdfiumVerClass()
NaN = float("nan")
PdfiumVerUnknown = PdfiumVer.scheme(NaN, NaN, NaN, NaN)

# def is_nan(value):
#     return isinstance(value, float) and value != value


def write_pdfium_info(dir, full_ver, origin, flags=(), n_commits=0, hash=None):
    if full_ver is PdfiumVerUnknown:
        log("Warning: pdfium version not known, will use NaN placeholders")
    info = dict(**full_ver._asdict(), n_commits=n_commits, hash=hash, origin=origin, flags=list(flags))
    write_json(dir/VersionFN, info)
    return info

def read_pdfium_info(dir):
    info = read_json(dir/VersionFN)
    full_ver = PdfiumVer.scheme(
        *(info.pop(k) for k in ("major", "minor", "build", "patch"))
    )
    return full_ver, info


def parse_given_tag(full_tag):
    
    info = dict()
    
    # note, `git describe --dirty` ignores new unregistered files
    tag = full_tag
    dirty = tag.endswith("-dirty")
    if dirty:
        tag = tag[:-len("-dirty")]
    tag, *id_parts = tag.split("-")
    
    ver_part, *beta_capture = tag.split("b")
    for v, k in zip(ver_part.split("."), ("major", "minor", "patch")):
        info[k] = int(v)
    assert len(beta_capture) in (0, 1)
    info["beta"] = int(beta_capture[0]) if beta_capture else None
    
    info.update(n_commits=0, hash=None, dirty=dirty)
    schema = ("n_commits", int), ("hash", str)
    for value, (key, cast) in zip(id_parts, schema):
        info[key] = cast(value)
    
    assert merge_tag(info, mode="git") == full_tag
    
    return info


def parse_git_tag():
    desc = run_cmd(["git", "describe", "--tags", "--dirty"], capture=True, cwd=ProjectDir)
    return parse_given_tag(desc)


def get_helpers_info():
    
    # TODO add some checks against record?
    
    have_git_describe = False
    if (ProjectDir/".git").exists():
        try:
            helpers_info = parse_git_tag()
        except subprocess.CalledProcessError as e:
            log(str(e))
            log("Version uncertain: git describe failure - possibly a shallow checkout")
        else:
            have_git_describe = True
            helpers_info["data_source"] = "git"
    else:
        log("Version uncertain: git repo not available.")
    
    if not have_git_describe:
        ver_file = ModuleDir_Helpers / VersionFN
        if ver_file.exists():
            log("Falling back to given version info (e.g. sdist).")
            helpers_info = read_json(ver_file)
            helpers_info["data_source"] = "given"
        else:
            log("Falling back to autorelease record.")
            record = read_json(AR_RecordFile)
            helpers_info = parse_given_tag(record["tag"])
            helpers_info["data_source"] = "record"
    
    return helpers_info


def merge_tag(info, mode):
    
    # some duplication with src/pypdfium2/version.py ...
    
    tag = ".".join([str(info[k]) for k in ("major", "minor", "patch")])
    if info['beta'] is not None:
        tag += f"b{info['beta']}"
    
    extra_info = []
    if info['n_commits'] > 0:
        extra_info += [f"{info['n_commits']}", f"{info['hash']}"]
    if info['dirty']:
        extra_info += ["dirty"]
    
    if extra_info:
        if mode == "git":
            tag += "-" + "-".join(extra_info)
        elif mode == "py":
            tag += "+" + ".".join(extra_info)
        else:
            log("Warning: Ignored post-tag desc. This should not happen in autorelease CI.")
    
    return tag


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


class UnhandledPlatformError (RuntimeError):
    pass


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
        except (UnhandledPlatformError, AttributeError) as e:
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
    
    def _handle_linux(self, archid, musl_ok=True):
        if self._libc_name == "glibc":
            return getattr(PlatNames, f"linux_{archid}")
        elif self._libc_name == "musl":
            if not musl_ok:
                raise UnhandledPlatformError(f"{archid} musl not supported with pdfium-binaries on setup. Please check PyPI for wheels.")
            return getattr(PlatNames, f"linux_musl_{archid}")
        elif _android_api():  # seems to imply self._libc_name == "libc"
            log("Android prior to PEP 738 (e.g. Termux)")
            self._system = SysNames.android
            return getattr(PlatNames, f"android_{archid}")
        else:
            raise UnhandledPlatformError(f"Linux with unhandled libc {self._libc_name!r}")
    
    def _get_platform(self):
        
        # TODO 32-bit interpreters running on 64-bit machines?
        
        if self._raw_system == "darwin":
            # platform.machine() is the actual architecture. sysconfig.get_platform() may return universal2, but by default we only use the arch-specific binaries.
            self._system = SysNames.darwin
            log(f"macOS {self._raw_machine}")  # platform.mac_ver()
            if self._raw_machine == "x86_64":
                return PlatNames.darwin_x64
            elif self._raw_machine == "arm64":
                return PlatNames.darwin_arm64
        
        elif self._raw_system == "windows":
            self._system = SysNames.windows
            log(f"windows {self._raw_machine}")  # platform.win32_ver()
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
                return self._handle_linux("arm32", musl_ok=False)
            elif self._raw_machine == "ppc64le":
                return self._handle_linux("ppc64le", musl_ok=False)
        
        elif self._raw_system == "android":  # PEP 738
            # The PEP isn't too explicit about the machine names, but based on related CPython PRs, it looks like platform.machine() retains the raw uname values as on Linux, whereas sysconfig.get_platform() will map to the wheel tags
            self._system = SysNames.android
            log(f"android {self._raw_machine}")  # sys.getandroidapilevel() platform.android_ver()
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
        
        raise UnhandledPlatformError(f"Unhandled platform: {self!r}")

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
    elif pl_name == PlatNames.linux_ppc64le:
        return _manylinux_tag("ppc64le")
    
    # pdfium-binaries statically link musl, so we can declare the lowest possible requirement.
    # The builds have been confirmed to work in a musllinux_1_1 container, as of Nov 2025.
    elif pl_name == PlatNames.linux_musl_x64:
        return "musllinux_1_1_x86_64"
    elif pl_name == PlatNames.linux_musl_x86:
        return "musllinux_1_1_i686"
    elif pl_name == PlatNames.linux_musl_arm64:
        return "musllinux_1_1_aarch64"
    
    # Android - see PEP 738 # Packaging
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


def run_cmd(command, cwd, capture=False, check=True, str_cast=True, stderr=None, **kwargs):
    
    if str_cast:
        command = [str(c) for c in command]
    
    log(f"{command} (cwd={cwd!r})")
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        if stderr is not None:
            # allow the caller to pass e.g. subprocess.STDOUT
            kwargs["stderr"] = stderr
    
    comp_process = subprocess.run(command, cwd=cwd, check=check, **kwargs)
    if capture:
        return comp_process.stdout.decode("utf-8").strip()
    else:
        return comp_process


def tar_extract_file(tar, path_or_member, dst_path):
    src_buf = tar.extractfile(path_or_member)
    assert src_buf is not None, f"Failed to extract {path_or_member}"
    with open(dst_path, "wb") as dst_buf:
        shutil.copyfileobj(src_buf, dst_buf)


@contextlib.contextmanager
def tmp_cwd_context(tmp_cwd):
    orig_cwd = os.getcwd()
    os.chdir(str(tmp_cwd.resolve()))
    try:
        yield
    finally:
        os.chdir(orig_cwd)


CTG_LIBPATTERN = "{prefix}{name}.{suffix}"

# TODO make version mandatory
def run_ctypesgen(
        target_path, headers_dir, flags=(),
        rt_paths=(f"./{CTG_LIBPATTERN}", ), ct_paths=(), univ_paths=(),
        search_sys_despite_libpaths=False,
        guard_symbols=False, no_srcinfo=False, version=None
    ):
    
    if USE_REFBINDINGS:
        log("Using reference bindings - this will bypass all bindings params. If this is not intentional, make sure ctypesgen is installed.")
        record_ver = PdfiumVer.pinned
        if version != record_ver:
            log(f"Warning: binary/bindings version mismatch ({version} != {record_ver}). This is ABI-unsafe!")
        shutil.copyfile(RefBindingsFile, target_path)
        return target_path
    
    # Import ctypesgen only in this function so it does not have to be available for other setup tasks
    import ctypesgen
    assert getattr(ctypesgen, "PYPDFIUM2_SPECIFIC", False), "pypdfium2 requires fork of ctypesgen"
    import ctypesgen.__main__
    
    # library loading
    args = ["-l", "pdfium"]
    if rt_paths:
        args += ["--rt-libpaths", *rt_paths]
    if univ_paths:
        args += ["--univ-libpaths", *univ_paths]
    if (rt_paths or univ_paths) and not search_sys_despite_libpaths:
        args += ["--no-system-libsearch"]
    if ct_paths:
        args += ["--ct-libpaths", *ct_paths]
    else:
        args += ["--no-load-library"]
    
    # style
    args += ["--no-macro-guards"]
    if not guard_symbols:
        args += ["--no-symbol-guards"]
    if no_srcinfo:
        args += ["--no-srcinfo"]
    
    # pre-processor - if not given, pypdfium2-ctypesgen will try to auto-select as available (gcc/clang)
    c_preproc = os.environ.get("CPP", None)
    if c_preproc:
        args += ["--cpp", c_preproc]
    if flags:
        args += ["-D"] + [PdfiumFlagsDict[f] for f in flags]
    if Host.system == SysNames.windows:
        # If we are on a Windows host, add the relevant define to expose Windows-only members.
        # Note, this is not currently active for our wheels, since we're packaging everything on Linux. It might be possible to divide packaging in native OS hosts in the future, or specify external headers for symbol spoofing.
        args += ["-D", "_WIN32"]
    
    # symbols - try to exclude some garbage aliases that get pulled in from struct tags
    # (this captures anything that ends with _, _t, or begins with _, and is not needed by other symbols)
    args += ["--symbol-rules", r"if_needed=\w+_$|\w+_t$|_\w+"]
    
    # input / output
    args += ["--headers"] + [h.name for h in sorted(headers_dir.glob("*.h"))] + ["-o", target_path]
    
    with tmp_cwd_context(headers_dir):
        ctypesgen.__main__.main([str(a) for a in args])


def _make_json_compat(obj):
    if isinstance(obj, dict):
        return {k: _make_json_compat(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_json_compat(v) for v in obj]
    elif isinstance(obj, Path):
        return str(obj)
    else:
        return obj


def build_pdfium_bindings(version, headers_dir=None, **kwargs):
    
    ver_path = DataDir_Bindings/VersionFN
    bind_path = BindingsFile
    if not headers_dir:
        headers_dir = DataDir_Bindings/"headers"
    
    # TODO register all defaults?
    curr_info = {"version": version, **kwargs}
    curr_info.pop("ct_paths", None)  # ignore
    curr_info.setdefault("flags", [])
    curr_info = _make_json_compat(curr_info)
    
    prev_ver = None
    if ver_path.exists():
        prev_info = read_json(ver_path)
        prev_ver = prev_info["version"]
        if bind_path.exists() and prev_info == curr_info:
            log(f"Using cached bindings")
            return
        else:
            log(f"Bindings cache state differs:", prev_info, curr_info, sep="\n")
    
    # try to reuse headers if only bindings params differ, not version
    if prev_ver == version and headers_dir.exists() and list(headers_dir.glob("fpdf*.h")):
        log("Using cached headers")
    else:
        log("Downloading headers...")
        mkdir(headers_dir)
        archive_url = f"{PdfiumURL}/+archive/refs/heads/chromium/{version}/public.tar.gz"
        archive_path = DataDir_Bindings / "pdfium_public.tar.gz"
        url_request.urlretrieve(archive_url, archive_path)
        with tarfile.open(archive_path) as tar:
            for m in tar.getmembers():
                if m.isfile() and re.fullmatch(r"fpdf(\w+)\.h", m.name, flags=re.ASCII):
                    tar_extract_file(tar, m, headers_dir/m.name)
        archive_path.unlink()
    
    log(f"Building bindings ...")
    bindings_path = DataDir_Bindings/BindingsFN
    run_ctypesgen(bindings_path, headers_dir, version=version, **kwargs)
    write_json(ver_path, curr_info)


def clean_platfiles():
    
    deletables = [
        ProjectDir / "build",
        ModuleDir_Raw / BindingsFN,
        ModuleDir_Raw / VersionFN,
    ]
    for pattern in LIBNAME_GLOBS:
        deletables += ModuleDir_Raw.glob(pattern)
    
    for fp in deletables:
        if fp.is_file():
            fp.unlink()
        elif fp.is_dir():
            shutil.rmtree(fp)


def build_pl_suffix(version, use_v8):
    return (PlatSpec_V8Sym if use_v8 else "") + PlatSpec_VerSep + str(version)


def parse_pl_spec(pl_spec):
    
    # TODO split up in individual env vars after all?
    
    req_ver, flags = None, ()
    if PlatSpec_VerSep in pl_spec:
        pl_spec, req_ver = pl_spec.rsplit(PlatSpec_VerSep)
    if pl_spec.endswith(PlatSpec_V8Sym):
        pl_spec, flags = pl_spec[:-len(PlatSpec_V8Sym)], ("V8", "XFA")
    
    subspec = None
    if not pl_spec or pl_spec == "auto":
        if Host.platform is None:
            log(str(Host._exc))
            pl_name = ExtPlats.fallback
        else:
            pl_name = Host.platform
    else:
        if "-" in pl_spec:
            pl_spec, subspec = pl_spec.split("-", maxsplit=1)
        if hasattr(ExtPlats, pl_spec):
            pl_name = getattr(ExtPlats, pl_spec)
        elif hasattr(PlatNames, pl_spec):
            pl_name = getattr(PlatNames, pl_spec)
        else:
            raise ValueError(f"Invalid binary spec '{pl_spec}'")
    
    if req_ver and req_ver.isnumeric():
        req_ver = int(req_ver)
    
    return pl_name, subspec, req_ver, flags


def parse_modspec(modspec):
    if modspec:
        modnames = modspec.split(",")
        assert set(modnames).issubset(ModulesAll)
        assert len(modnames) in (1, 2)
    else:
        modnames = ModulesAll
    return modnames


def get_next_changelog(flush=False):
    
    content = ChangelogStaging.read_text()
    pos = content.index("\n", content.index("# Changelog")) + 1
    header = content[:pos].strip() + "\n"
    devel_msg = content[pos:].strip()
    if devel_msg:
        devel_msg += "\n"
    
    if flush:
        ChangelogStaging.write_text(header)
    
    return devel_msg


def git_apply_patch(patch, cwd, git_args=()):
    run_cmd(["git", *git_args, "apply", "--ignore-space-change", "--ignore-whitespace", "-v", patch], cwd=cwd, check=True)


def git_clone_rev(url, rev, target_dir, depth=1):
    # https://stackoverflow.com/questions/31278902/how-to-shallow-clone-a-specific-commit-with-depth-1
    mkdir(target_dir)
    depth_param = ["--depth", str(depth)] if depth else []
    run_cmd(["git", "-c", "advice.defaultBranchName=false", "init"], cwd=target_dir)
    run_cmd(["git", "remote", "add", "origin", url], cwd=target_dir)
    run_cmd(["git", "fetch", *depth_param, "origin", rev], cwd=target_dir)
    run_cmd(["git", "-c", "advice.detachedHead=false", "checkout", "FETCH_HEAD"], cwd=target_dir)


def _to_gn(value):
    if isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, list):
        return f"[{','.join(_to_gn(v) for v in value)}]"
    else:
        raise TypeError(f"Not sure how to serialize type {type(value).__name__}")

def serialize_gn_config(config_dict):
    parts = []
    for key, value in config_dict.items():
        parts.append(f"{key} = {_to_gn(value)}")
    result = "\n".join(parts)
    log(f"\nBuild config:\n{result}\n")
    return result


_SHIMHEADERS_URL = "https://raw.githubusercontent.com/chromium/chromium/{rev}/tools/generate_shim_headers/generate_shim_headers.py"

def get_shimheaders_tool(pdfium_dir, rev="main"):

    tools_dir = pdfium_dir / "tools" / "generate_shim_headers"
    shimheaders_file = tools_dir / "generate_shim_headers.py"
    shimheaders_url = _SHIMHEADERS_URL.format(rev=rev)

    if not shimheaders_file.exists():
        log(f"Downloading {shimheaders_file.name} at revision {rev}")
        mkdir(tools_dir)
        url_request.urlretrieve(shimheaders_url, shimheaders_file)


def purge_dir(dir):
    if dir.exists():
        shutil.rmtree(dir)
    dir.mkdir(parents=True)


def git_get_hash(repo_dir, n_digits=None):
    short = f"--short={n_digits}" if n_digits else "--short"
    return "g" + run_cmd(["git", "rev-parse", short, "HEAD"], cwd=repo_dir, capture=True)


def handle_sbuild_vers(short_ver):
    if short_ver == "main":
        full_ver = PdfiumVer.get_latest_upstream()
        pdfium_rev = short_ver
        chromium_rev = short_ver
    else:
        assert str(short_ver).isnumeric()
        full_ver = PdfiumVer.to_full(short_ver)
        full_ver_str = str(full_ver)
        pdfium_rev = f"chromium/{short_ver}"
        chromium_rev = full_ver_str
    return full_ver, pdfium_rev, chromium_rev


def pack_sourcebuild(
        pdfium_dir, build_dir, sub_target,
        full_ver, build_ver=None, post_ver=None,
        load_lib=True,
    ):
    log("Packing data files for sourcebuild...")
    
    if not post_ver:
        assert build_ver
        if build_ver == "main":
            log("Warning: Don't know how to get number of commits with shallow checkout. A NaN placeholder will be set.")
            post_ver = dict(n_commits=NaN, hash=git_get_hash(pdfium_dir, n_digits=11))
        else:
            post_ver = dict(n_commits=0, hash=None)
    
    dest_dir = DataDir/ExtPlats.sourcebuild
    purge_dir(dest_dir)
    
    libname = libname_for_system(Host.system)
    shutil.copy(build_dir/libname, dest_dir/libname)
    
    # We want to use local headers instead of downloading with build_pdfium_bindings(), therefore call run_ctypesgen() directly
    ct_paths = (dest_dir/CTG_LIBPATTERN, ) if load_lib else ()
    run_ctypesgen(dest_dir/BindingsFN, headers_dir=pdfium_dir/"public", ct_paths=ct_paths, version=full_ver.build)
    write_pdfium_info(dest_dir, full_ver, origin=f"sourcebuild-{sub_target}", **post_ver)
    
    return full_ver, post_ver


def bootstrap_ninja(skip_if_present=True):
    if skip_if_present and shutil.which("ninja"):
        log("+ ninja found.")
        return
    # https://github.com/scikit-build/ninja-python-distributions
    log("- ninja not found, installing...")
    run_cmd([sys.executable, "-m", "pip", "install", "ninja"], cwd=None)

def make_executable(path):
    if sys.platform.startswith("win32"):
        return
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def bootstrap_gn(target_dir=None, skip_if_present=True):
    if skip_if_present and shutil.which("gn"):
        log("+ gn found.")
        return
    
    log("- gn not found, attempt to build from scratch...")
    if target_dir is None:
        target_dir = Host.local_bin
    
    gn_dir = ProjectDir/"sbuild"/"gn"
    url = "https://gn.googlesource.com/gn/"
    rev = "a0c5124a50608595a9aadebc4297e854ebd32c53"
    if not gn_dir.exists():
        git_clone_rev(url, rev, gn_dir, depth=1)
        git_apply_patch(PatchDir/"gn_build.patch", cwd=gn_dir)
    
    os.environ["CXX"] = "g++"
    run_cmd(["python3", "build/gen.py", "--no-last-commit-position", "--no-static-libstdc++", "--allow-warnings"], cwd=gn_dir)
    run_cmd(["ninja", "-C", "out", "gn"], cwd=gn_dir)
    del os.environ["CXX"]
    
    shutil.copyfile(gn_dir/"out"/"gn", target_dir/"gn")
    make_executable(target_dir/"gn")

def bootstrap_buildtools():
    log("Bootstrapping build tools...")
    bootstrap_ninja()
    bootstrap_gn()


def autopatch(file, pattern, repl, is_regex, exp_count=None):
    log(f"Patch {pattern!r} -> {repl!r} (is_regex={is_regex}) on {file}")
    content = file.read_text()
    if is_regex:
        content, n_subs = re.subn(pattern, repl, content)
    else:
        n_subs = content.count(pattern)
        content = content.replace(pattern, repl)
    if exp_count is not None:
        assert n_subs == exp_count
    file.write_text(content)

def autopatch_dir(dir, globexpr, pattern, repl, is_regex, exp_count=None):
    for file in dir.glob(globexpr):
        autopatch(file, pattern, repl, is_regex, exp_count)

def shared_autopatches(pdfium_dir):
    autopatch_dir(
        pdfium_dir/"public"/"cpp", "*.h",
        r'"public/(.+)"', r'"../\1"',
        is_regex=True, exp_count=None,
    )
    # bundle dependencies (e.g. abseil) into the pdfium DLL
    autopatch(
        pdfium_dir/"BUILD.gn",
        'component("pdfium")',
        'shared_library("pdfium")',
        is_regex=False, exp_count=1,
    )
    autopatch(
        pdfium_dir/"public"/"fpdfview.h",
        "#if defined(COMPONENT_BUILD)",
        "#if 1  // defined(COMPONENT_BUILD)",
        is_regex=False, exp_count=1,
    )
