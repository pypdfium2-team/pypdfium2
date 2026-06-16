# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import re
import sys
import json
import shutil
import tarfile
import platform
import argparse
import functools
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

# The PDFium versions our build scripts have last been tested with.
# Ideally, they should be close to the release version in autorelease/record.json
# To bump these versions, first test locally and update any patches as needed.
# Then, make a branch and run "Sourcebuild", "Sourcebuild Native" and "CIBW" on CI to see if all targets continue to work.
# Commit the new version to the main branch only when all is green. Better stay on an older version for a while than break a target.
# Updating and testing the patch sets can be a lot of work, so we might not want to do this too frequrently.
SBUILD_NATIVE_PIN = 7891
SBUILD_TOOLCHAINED_PIN = 7891

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

def plat_to_system(pl_name):
    if pl_name == ExtPlats.sourcebuild:
        # Note, this may be None if on an unknown host
        return Host.system
    # other ExtPlats intentionally not handled here
    return getattr(SysNames, pl_name.split("_", maxsplit=1)[0])

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
        log(f"Unhandled system {Host._raw_system!r} ({sys.platform!r})" + " - assuming 'lib{}.so' pattern. Set $LIBNAME_PATTERN if this is not right.")
        return f"lib{name}.so"


def mkdir(path, exist_ok=True, parents=True):
    path.mkdir(exist_ok=exist_ok, parents=parents)

def read_json(fp):
    with open(fp, "r") as buf:
        return json.load(buf)

def write_json(fp, data, indent=2):
    with open(fp, "w") as buf:
        return json.dump(data, buf, indent=indent)

def env_prepend(key, value, sep):
    tail = os.environ.get(key, "")
    if tail:
        tail = sep + tail
    os.environ[key] = value + tail

def env_append(key, value, sep):
    head = os.environ.get(key, "")
    if head:
        head += sep
    os.environ[key] = head + value

def set_envs(**kwargs):
    for key, value in kwargs.items():
        os.environ[key] = value

def query_envs(**kwargs):
    return {k: os.environ.get(k, d) for k, d in kwargs.items()}


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
    
    if (ProjectDir/".git").exists():
        try:
            helpers_info = parse_git_tag()
        except subprocess.CalledProcessError as e:
            log(str(e))
        else:
            helpers_info["data_source"] = "git"
            return helpers_info
    
    log("Unable to use SCM version (e.g. tarball or shallow clone).")
    
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
            elif self._raw_machine in ("armv7l", "armv8l"):
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


def run_cmd(command, cwd, capture=False, check=True, str_cast=True, stderr=None, silent=False, **kwargs):
    
    if str_cast:
        command = [str(c) for c in command]
    if not silent:
        log(f"{command} (cwd={cwd!r})")
    
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        if stderr is not None:
            # allow the caller to pass e.g. subprocess.STDOUT
            kwargs["stderr"] = stderr
    elif silent:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
    
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
        guard_symbols=False, no_srcinfo=False,
        windows_cross=False, version=None,
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
    if ct_paths:
        args += ["--ct-libpaths", *ct_paths]
    if univ_paths:
        args += ["--univ-libpaths", *univ_paths]
    if not (ct_paths or univ_paths):
        args += ["--no-load-library"]
    if (rt_paths or univ_paths) and not search_sys_despite_libpaths:
        args += ["--no-system-libsearch"]
    
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
    
    # include windows-only members (e.g. refbindings, cross-packaging)
    # see the comments in utils/spoof/windows.h for more info on this approach
    # actually, also do this on windows natively to save ctypesgen from a lot of trouble processing windows system headers where it keeps running into syntax errors
    is_windows_host = sys.platform.startswith("win32")
    if windows_cross and not is_windows_host:
        args += ["-D", "_WIN32"]
    if windows_cross or is_windows_host:
        args += ["-I", ProjectDir/"utils"/"spoof"]
    
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


def purge_dir(dir):
    if dir.exists():
        shutil.rmtree(dir)
    dir.mkdir(parents=True)
