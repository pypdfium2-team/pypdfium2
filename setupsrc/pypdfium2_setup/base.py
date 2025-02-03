# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import re
import sys
import json
import shutil
import tarfile
import platform
import functools
import sysconfig
import subprocess
import contextlib
from pathlib import Path
from collections import namedtuple
import urllib.request as url_request

PlatSpec_EnvVar = "PDFIUM_PLATFORM"
PlatSpec_VerSep = ":"
PlatSpec_V8Sym  = "-v8"

BindSpec_EnvVar = "PDFIUM_BINDINGS"
BindTarget_Ref  = "reference"
BindTarget = os.environ.get(BindSpec_EnvVar, None)

ModulesSpec_EnvVar = "PYPDFIUM_MODULES"
ModuleRaw          = "raw"
ModuleHelpers      = "helpers"
ModulesAll         = (ModuleRaw, ModuleHelpers)

BindingsFN = "bindings.py"
VersionFN  = "version.json"

ProjectDir        = Path(__file__).parents[2].resolve()
DataDir           = ProjectDir / "data"
DataDir_Bindings  = DataDir / "bindings"
SourcebuildDir    = ProjectDir / "sourcebuild"
ModuleDir_Raw     = ProjectDir / "src" / "pypdfium2_raw"
ModuleDir_Helpers = ProjectDir / "src" / "pypdfium2"
Changelog         = ProjectDir / "docs" / "devel" / "changelog.md"
ChangelogStaging  = ProjectDir / "docs" / "devel" / "changelog_staging.md"
HAVE_GIT_REPO     = (ProjectDir / ".git").exists()

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

REFBINDINGS_FLAGS = ("V8", "XFA", "SKIA")


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
    sdist       = "sdist"

class PlatNames:
    # - Attribute names and values are expected to match
    # - Platform names are expected to start with the corresponding system name
    darwin_x64       = SysNames.darwin  + "_x64"
    darwin_arm64     = SysNames.darwin  + "_arm64"
    darwin_universal = SysNames.darwin  + "_universal"
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
# export PLATFORMS=(darwin_universal android_arm32 android_x64 android_x86 ios_arm64_dev ios_arm64_simu ios_x64_simu)
# for PLAT in ${PLATFORMS[@]}; do echo $PLAT; ./run emplace $PLAT; PDFIUM_PLATFORM=$PLAT python3 -m build -wxn; done
PdfiumBinariesMap.update({
    PlatNames.darwin_universal: "mac-univ",
    PlatNames.android_arm64:    "android-arm64",
    PlatNames.android_arm32:    "android-arm",
    PlatNames.android_x64:      "android-x64",
    PlatNames.android_x86:      "android-x86",
    PlatNames.ios_arm64_dev:    "ios-device-arm64",
    PlatNames.ios_arm64_simu:   "ios-simulator-arm64",
    PlatNames.ios_x64_simu:     "ios-simulator-x64",
})


# Map system to pdfium shared library name
def libname_for_system(system):
    if system == SysNames.windows:
        return "pdfium.dll"
    elif system in (SysNames.darwin, SysNames.ios):
        return "libpdfium.dylib"
    elif system in (SysNames.linux, SysNames.android):
        return "libpdfium.so"
    else:
        # TODO fallback logic if system is None?
        raise ValueError(f"Unhandled system {system!r}")

AllLibnames = ["pdfium.dll", "libpdfium.dylib", "libpdfium.so"]


if sys.version_info < (3, 8):
    # NOTE alternatively, we could write our own cached property backport with python's descriptor protocol
    def cached_property(func):
        return property( functools.lru_cache(maxsize=1)(func) )
else:
    cached_property = functools.cached_property


class PdfiumVer:
    
    scheme = namedtuple("PdfiumVer", ("major", "minor", "build", "patch"))
    _refs_cache = {"lines": None, "dict": {}, "cursor": None}
    
    @staticmethod
    @functools.lru_cache(maxsize=1)
    def get_latest():
        git_ls = run_cmd(["git", "ls-remote", f"{ReleaseRepo}.git"], cwd=None, capture=True)
        tag = git_ls.split("\t")[-1]
        return int( tag.split("/")[-1] )
    
    @classmethod
    def to_full(cls, v_short):
        
        # FIXME The ls-remote call is fairly expensive. While cached in memory for a process lifetime, it can cause a significant slowdown for consecutive process runs.
        # There may be multiple ways to improve this, like adding some disk cache to ensure it would only be called once for a whole session, or maybe adding a second strategy that would parse the pdfium-binaries VERSION file, and use the chromium refs only for sourcebuild.
        
        v_short = int(v_short)
        rc = cls._refs_cache
        
        if rc["lines"] is None:
            print(f"Fetching chromium refs ...", file=sys.stderr)
            ChromiumURL = "https://chromium.googlesource.com/chromium/src"
            rc["lines"] = run_cmd(["git", "ls-remote", "--sort", "-version:refname", "--tags", ChromiumURL, '*.*.*.0'], cwd=None, capture=True).split("\n")
        
        if rc["cursor"] is None or rc["cursor"] > v_short:
            for i, line in enumerate(rc["lines"]):
                ref = line.split("\t")[-1].rsplit("/", maxsplit=1)[-1]
                full_ver = cls.scheme(*[int(v) for v in ref.split(".")])
                rc["dict"][full_ver.build] = full_ver
                if full_ver.build == v_short:
                    rc["cursor"] = full_ver.build
                    rc["lines"] = rc["lines"][i+1:]
                    break
        
        full_ver = rc["dict"][v_short]
        print(f"Resolved {v_short} -> {full_ver}", file=sys.stderr)
        
        return full_ver


def read_json(fp):
    with open(fp, "r") as buf:
        return json.load(buf)

def write_json(fp, data, indent=2):
    with open(fp, "w") as buf:
        return json.dump(data, buf, indent=indent)


def write_pdfium_info(dir, build, origin, flags=(), n_commits=0, hash=None):
    info = dict(**PdfiumVer.to_full(build)._asdict(), n_commits=n_commits, hash=hash, origin=origin, flags=list(flags))
    write_json(dir/VersionFN, info)
    return info


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
            print("Warning: Ignored post-tag desc. This should not happen in autorelease CI.", file=sys.stderr)
    
    return tag


def plat_to_system(pl_name):
    if pl_name == ExtPlats.sourcebuild:
        # FIXME If doing a sourcebuild on an unknown host system, this returns None, which will cause binary detection code to fail (we need to know the platform-specific binary name) - handle this downstream with fallback value?
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
        self._system_name = platform.system().lower()
        self._machine_name = platform.machine().lower()
        
        # empty slots
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
        if self.platform is not None:
            return plat_to_system(self.platform)
        else:
            return None
    
    def __repr__(self):
        info = f"{self._system_name} {self._machine_name}"
        if self._system_name == "linux" and self._libc_name:
            info += f", {self._libc_name} {self._libc_ver}"
        return f"<Host: {info}>"
    
    def _handle_linux(self, archid):
        if self._libc_name == "glibc":
            return getattr(PlatNames, f"linux_{archid}")
        elif self._libc_name == "musl":
            return getattr(PlatNames, f"linux_musl_{archid}")
        elif _android_api():  # seems to imply self._libc_name == "libc"
            print("Android prior to PEP 738 (e.g. Termux)", file=sys.stderr)
            return getattr(PlatNames, f"android_{archid}")
        else:
            raise RuntimeError(f"Linux with unhandled libc {self._libc_name!r}.")
    
    def _get_platform(self):
        
        # TODO 32-bit interpreters running on 64-bit machines?
        
        if self._system_name == "darwin":
            # platform.machine() is the actual architecture. sysconfig.get_platform() may return universal2, but by default we only use the arch-specific binaries.
            print(f"macOS {self._machine_name} {platform.mac_ver()}", file=sys.stderr)
            if self._machine_name == "x86_64":
                return PlatNames.darwin_x64
            elif self._machine_name == "arm64":
                return PlatNames.darwin_arm64
        
        elif self._system_name == "windows":
            print(f"windows {self._machine_name} {platform.win32_ver()}", file=sys.stderr)
            if self._machine_name == "amd64":
                return PlatNames.windows_x64
            elif self._machine_name == "x86":
                return PlatNames.windows_x86
            elif self._machine_name == "arm64":
                return PlatNames.windows_arm64
        
        elif self._system_name == "linux":
            self._libc_name, self._libc_ver = _get_libc_info()
            print(f"linux {self._machine_name} {self._libc_name, self._libc_ver}", file=sys.stderr)
            if self._machine_name == "x86_64":
                return self._handle_linux("x64")
            elif self._machine_name == "i686":
                return self._handle_linux("x86")
            elif self._machine_name == "aarch64":
                return self._handle_linux("arm64")
            elif self._machine_name == "armv7l":
                if self._libc_name == "musl":
                    raise RuntimeError(f"armv7l: musl not supported at this time.")
                return self._handle_linux("arm32")
        
        elif self._system_name == "android":  # PEP 738
            # The PEP isn't too explicit about the machine names, but based on related CPython PRs, it looks like platform.machine() retains the raw uname values as on Linux, whereas sysconfig.get_platform() will map to the wheel tags
            print(f"android {self._machine_name} {sys.getandroidapilevel()} {platform.android_ver()}", file=sys.stderr)
            if self._machine_name == "aarch64":
                return PlatNames.android_arm64
            elif self._machine_name == "armv7l":
                return PlatNames.android_arm32
            elif self._machine_name == "x86_64":
                return PlatNames.android_x64
            elif self._machine_name == "i686":
                return PlatNames.android_x86
        
        elif self._system_name in ("ios", "ipados"):  # PEP 730
            # This is currently untested. We don't have access to an iOS device, so this is basically guessed from what the PEP mentions.
            ios_ver = platform.ios_ver()
            print(f"{self._system_name} {self._machine_name} {ios_ver}", file=sys.stderr)
            if self._machine_name == "arm64":
                return PlatNames.ios_arm64_simu if ios_ver.is_simulator else PlatNames.ios_arm64_dev
            elif self._machine_name == "x86_64":
                assert ios_ver.is_simulator, "iOS x86_64 can only be simulator"
                return PlatNames.ios_x64_simu
        
        raise RuntimeError(f"Unhandled platform: {self!r}")

Host = _host_platform()


def _manylinux_tag(arch, glibc="2_17"):
    # see BUG(203) for discussion of glibc requirement
    return f"manylinux_{glibc}_{arch}.manylinux2014_{arch}"

def get_wheel_tag(pl_name):
    
    if pl_name == PlatNames.darwin_x64:
        # pdfium-binaries/steps/05-configure.sh defines `mac_deployment_target = "10.13.0"`
        # "intel" instead of "x86_64" might work too, but I think it's considered legacy
        return "macosx_10_13_x86_64"
    elif pl_name == PlatNames.darwin_arm64:
        # macOS 11 is the first version available on arm64
        return "macosx_11_0_arm64"
    elif pl_name == PlatNames.darwin_universal:
        # universal binary format (combo of x64 and arm64) - we prefer arch-specific wheels, but allow callers to build a universal wheel if they want to
        return "macosx_10_13_universal2"
    
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
    
    elif pl_name == PlatNames.linux_musl_x64:
        return "musllinux_1_1_x86_64"
    elif pl_name == PlatNames.linux_musl_x86:
        return "musllinux_1_1_i686"
    elif pl_name == PlatNames.linux_musl_arm64:
        return "musllinux_1_1_aarch64"
    
    # Android - see PEP 738 # Packaging
    # At this time, we only build wheels for android_arm64, but handle the others as well so the code is ready if we want to in the future (or in case callers want to build their own wheels)
    elif pl_name == PlatNames.android_arm64:
        return "android_21_arm64_v8a"
    elif pl_name == PlatNames.android_arm32:
        return "android_21_armeabi_v7a"
    elif pl_name == PlatNames.android_x64:
        return "android_21_x86_64"
    elif pl_name == PlatNames.android_x86:
        return "android_21_x86"
    
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
            tag = tag[:-len("universal2")] + Host._machine_name
        return tag
    
    else:
        raise ValueError(f"Unhandled platform name {pl_name}")


def run_cmd(command, cwd, capture=False, check=True, str_cast=True, **kwargs):
    
    if str_cast:
        command = [str(c) for c in command]
    
    print(f"{command} (cwd={cwd!r})", file=sys.stderr)
    if capture:
        kwargs.update( dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT) )
    
    comp_process = subprocess.run(command, cwd=cwd, check=check, **kwargs)
    if capture:
        return comp_process.stdout.decode("utf-8").strip()
    else:
        return comp_process


def tar_extract_file(tar, src, dst_path):
    src_buf = tar.extractfile(src)  # src: path str or tar member object
    with open(dst_path, "wb") as dst_buf:
        shutil.copyfileobj(src_buf, dst_buf)


PdfiumFlagsDict = {
    "V8": "PDF_ENABLE_V8",
    "XFA": "PDF_ENABLE_XFA",
    "SKIA": "PDF_USE_SKIA",
}


@contextlib.contextmanager
def tmp_cwd_context(tmp_cwd):
    orig_cwd = os.getcwd()
    os.chdir(str(tmp_cwd.resolve()))
    try:
        yield
    finally:
        os.chdir(orig_cwd)


def run_ctypesgen(target_dir, headers_dir, flags=(), compile_lds=(), run_lds=(".", ), search_sys_despite_libdirs=False, guard_symbols=False, no_srcinfo=False):
    # Import ctypesgen only in this function so it does not have to be available for other setup tasks
    import ctypesgen
    assert getattr(ctypesgen, "PYPDFIUM2_SPECIFIC", False), "pypdfium2 requires fork of ctypesgen"
    import ctypesgen.__main__
    
    # library loading
    args = ["-l", "pdfium"]
    if run_lds:
        args += ["--runtime-libdirs", *run_lds]
        if not search_sys_despite_libdirs:
            args += ["--no-system-libsearch"]
    if compile_lds:
        args += ["--compile-libdirs", *compile_lds]
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
    args += ["--headers"] + [h.name for h in sorted(headers_dir.glob("*.h"))] + ["-o", target_dir/BindingsFN]
    
    with tmp_cwd_context(headers_dir):
        ctypesgen.__main__.main([str(a) for a in args])


def build_pdfium_bindings(version, headers_dir=None, **kwargs):
    defaults = dict(flags=(), run_lds=(".", ), guard_symbols=False)
    for k, v in defaults.items():
        kwargs.setdefault(k, v)
    
    ver_path = DataDir_Bindings/VersionFN
    bind_path = DataDir_Bindings/BindingsFN
    if not headers_dir:
        headers_dir = DataDir_Bindings / "headers"
    
    # quick and dirty patch to allow using the pre-built bindings instead of calling ctypesgen
    # TODO move handler into run_ctypesgen on behalf of sourcebuild?
    # FIXME Bindings version file is ignored by upstream code, e.g. we don't handle the case of mismatched bindings/binary and only include the binary version in the end. Strictly speaking we might have to split the current PDFIUM_INFO in BINDINGS_INFO and BINARY_INFO ...
    if BindTarget == BindTarget_Ref:
        print("Using reference bindings as requested by env var. This will bypass all bindings params.", file=sys.stderr)
        record = read_json(AR_RecordFile)
        bindings_ver = record["pdfium"]
        if bindings_ver != version:
            print(f"Warning: ABI version mismatch (bindings {bindings_ver}, binary target {version}). This is potentially unsafe!", file=sys.stderr)
        flags_diff = set(kwargs["flags"]).difference(REFBINDINGS_FLAGS)
        if flags_diff:  # == not set(...).issubset(...)
            print(f"Warning: The following requested flags are not available in the reference bindings and will be discarded: {flags_diff}")
        DataDir_Bindings.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(RefBindingsFile, DataDir_Bindings/BindingsFN)
        write_json(ver_path, dict(version=bindings_ver, flags=REFBINDINGS_FLAGS, run_lds=["."], source="reference"))
        return
    
    curr_info = dict(
        version = version,
        flags = list(kwargs["flags"]),
        run_lds = list(kwargs["run_lds"]),
        guard_symbols = kwargs["guard_symbols"],
        source = "generated",
    )
    prev_ver = None
    if ver_path.exists():
        prev_info = read_json(ver_path)
        prev_ver = prev_info["version"]
        if prev_info == curr_info and bind_path.exists():
            print(f"Using cached bindings", file=sys.stderr)
            return
    
    # We try to reuse headers if only bindings params differ, not version. Note that headers don't currently have an own version file; we reuse the bindings version file for simplicity.
    if prev_ver == version and headers_dir.exists() and list(headers_dir.glob("fpdf*.h")):
        print("Using cached headers", file=sys.stderr)
    else:
        print("Downloading headers...", file=sys.stderr)
        headers_dir.mkdir(parents=True, exist_ok=True)
        archive_url = f"{PdfiumURL}/+archive/refs/heads/chromium/{version}/public.tar.gz"
        archive_path = DataDir_Bindings / "pdfium_public.tar.gz"
        url_request.urlretrieve(archive_url, archive_path)
        with tarfile.open(archive_path) as tar:
            for m in tar.getmembers():
                if m.isfile() and re.fullmatch(r"fpdf(\w+)\.h", m.name, flags=re.ASCII):
                    tar_extract_file(tar, m, headers_dir/m.name)
        archive_path.unlink()
    
    print(f"Building bindings ...", file=sys.stderr)
    run_ctypesgen(DataDir_Bindings, headers_dir, **kwargs)
    write_json(ver_path, curr_info)


def clean_platfiles():
    
    deletables = [
        ProjectDir / "build",
        ModuleDir_Raw / BindingsFN,
        ModuleDir_Raw / VersionFN,
    ]
    deletables += [ModuleDir_Raw / fn for fn in AllLibnames]
    
    for fp in deletables:
        if fp.is_file():
            fp.unlink()
        elif fp.is_dir():
            shutil.rmtree(fp)


def get_helpers_info():
    
    # TODO add some checks against record?
    
    have_git_describe = False
    if HAVE_GIT_REPO:
        try:
            helpers_info = parse_git_tag()
        except subprocess.CalledProcessError as e:
            print(str(e), file=sys.stderr)
            print("Version uncertain: git describe failure - possibly a shallow checkout", file=sys.stderr)
        else:
            have_git_describe = True
            helpers_info["data_source"] = "git"
    else:
        print("Version uncertain: git repo not available.")
    
    if not have_git_describe:
        ver_file = ModuleDir_Helpers / VersionFN
        if ver_file.exists():
            print("Falling back to given version info (e.g. sdist).", file=sys.stderr)
            helpers_info = read_json(ver_file)
            helpers_info["data_source"] = "given"
        else:
            print("Falling back to autorelease record.", file=sys.stderr)
            record = read_json(AR_RecordFile)
            helpers_info = parse_given_tag(record["tag"])
            helpers_info["data_source"] = "record"
    
    return helpers_info


def build_pl_suffix(version, use_v8):
    return (PlatSpec_V8Sym if use_v8 else "") + PlatSpec_VerSep + str(version)


def parse_pl_spec(pl_spec):
    
    # TODOs
    # - targets integration is inflexible, need to restructure
    # - add way to pass through package provider with system target?
    
    do_prepare = True
    if pl_spec.startswith("prepared!"):
        pl_spec = pl_spec[len("prepared!"):]  # removeprefix
        do_prepare = False
    
    req_ver = None
    use_v8 = False
    if PlatSpec_VerSep in pl_spec:
        pl_spec, req_ver = pl_spec.rsplit(PlatSpec_VerSep)
    if pl_spec.endswith(PlatSpec_V8Sym):
        pl_spec = pl_spec[:-len(PlatSpec_V8Sym)]
        use_v8 = True
    
    if not pl_spec or pl_spec == "auto":
        pl_name = Host.platform
        if pl_name is None:
            # delegate handling of unknown platforms to the caller (setup.py)
            return None
    elif hasattr(ExtPlats, pl_spec):
        pl_name = getattr(ExtPlats, pl_spec)
    elif hasattr(PlatNames, pl_spec):
        pl_name = getattr(PlatNames, pl_spec)
    else:
        raise ValueError(f"Invalid binary spec '{pl_spec}'")
        
    if req_ver:
        assert req_ver.isnumeric()
        req_ver = int(req_ver)
    else:
        assert pl_name != ExtPlats.system and do_prepare, "Version must be given explicitly for system or prepared!... targets"
        req_ver = PdfiumVer.get_latest()
    
    return do_prepare, pl_name, req_ver, use_v8


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
