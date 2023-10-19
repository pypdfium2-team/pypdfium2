# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# No external dependencies shall be imported in this file
# TODO improve consistency of variable names; think about variables to move in/out

import re
import sys
import json
import shutil
import platform
import functools
import sysconfig
import subprocess
from pathlib import Path
import urllib.request as url_request

sys.path.insert(0, str(Path(__file__).parents[1]))

# TODO(apibreak) consider renaming PDFIUM_PLATFORM to PDFIUM_BINARY ?
PlatSpec_EnvVar   = "PDFIUM_PLATFORM"
PlatSpec_VerSep   = ":"
PlatSpec_V8Sym    = "-v8"
PlatTarget_None   = "none"   # sdist, no binary
PlatTarget_System = "system" # pdfium provided by system (if available)
PlatTarget_Auto   = "auto"   # pdfium-binaries for host
VerTarget_Latest  = "latest"

ModulesSpec_EnvVar = "PYPDFIUM_MODULES"
ModuleRaw          = "raw"
ModuleHelpers      = "helpers"
ModulesAll         = (ModuleRaw, ModuleHelpers)

# NOTE if renaming BindingsFN, also rename `bindings/$FILE`
BindingsFN = "bindings.py"
VersionFN  = "version.json"

ProjectDir        = Path(__file__).parents[2]
DataDir           = ProjectDir / "data"
SourcebuildDir    = ProjectDir / "sourcebuild"
ModuleDir_Raw     = ProjectDir / "src" / "pypdfium2_raw"
ModuleDir_Helpers = ProjectDir / "src" / "pypdfium2"
Changelog         = ProjectDir / "docs" / "devel" / "changelog.md"
ChangelogStaging  = ProjectDir / "docs" / "devel" / "changelog_staging.md"
HAVE_GIT_REPO     = (ProjectDir / ".git").exists()

AutoreleaseDir   = ProjectDir / "autorelease"
AR_RecordFile    = AutoreleaseDir / "record.json"  # TODO verify contents on before merge
AR_ConfigFile    = AutoreleaseDir / "config.json"
RefBindingsFile  = AutoreleaseDir / BindingsFN

RepositoryURL  = "https://github.com/pypdfium2-team/pypdfium2"
PdfiumURL      = "https://pdfium.googlesource.com/pdfium"
DepotToolsURL  = "https://chromium.googlesource.com/chromium/tools/depot_tools.git"
ReleaseRepo    = "https://github.com/bblanchon/pdfium-binaries"
ReleaseURL     = ReleaseRepo + "/releases/download/chromium%2F"
ReleaseInfoURL = ReleaseURL.replace("github.com/", "api.github.com/repos/").replace("download/", "tags/")


class SysNames:
    linux   = "linux"
    darwin  = "darwin"
    windows = "windows"


# TODO align with either python or google platform names?
class PlatNames:
    # - Attribute names and values are expected to match
    # - Platform names are expected to start with the corresponding system name
    linux_x64        = SysNames.linux   + "_x64"
    linux_x86        = SysNames.linux   + "_x86"
    linux_arm64      = SysNames.linux   + "_arm64"
    linux_arm32      = SysNames.linux   + "_arm32"
    linux_musl_x64   = SysNames.linux   + "_musl_x64"
    linux_musl_x86   = SysNames.linux   + "_musl_x86"
    linux_musl_arm64 = SysNames.linux   + "_musl_arm64"
    darwin_x64       = SysNames.darwin  + "_x64"
    darwin_arm64     = SysNames.darwin  + "_arm64"
    windows_x64      = SysNames.windows + "_x64"
    windows_x86      = SysNames.windows + "_x86"
    windows_arm64    = SysNames.windows + "_arm64"
    sourcebuild      = "sourcebuild"


ReleaseNames = {
    PlatNames.darwin_x64       : "mac-x64",
    PlatNames.darwin_arm64     : "mac-arm64",
    PlatNames.linux_x64        : "linux-x64",
    PlatNames.linux_x86        : "linux-x86",
    PlatNames.linux_arm64      : "linux-arm64",
    PlatNames.linux_arm32      : "linux-arm",
    PlatNames.linux_musl_x64   : "linux-musl-x64",
    PlatNames.linux_musl_x86   : "linux-musl-x86",
    PlatNames.linux_musl_arm64 : "linux-musl-arm64",  # not V8 AOTW
    PlatNames.windows_x64      : "win-x64",
    PlatNames.windows_x86      : "win-x86",
    PlatNames.windows_arm64    : "win-arm64",
}

LibnameForSystem = {
    SysNames.linux:   "libpdfium.so",
    SysNames.darwin:  "libpdfium.dylib",
    SysNames.windows: "pdfium.dll",
}

BinaryPlatforms = list(ReleaseNames.keys())
BinarySystems   = list(LibnameForSystem.keys())
MainLibnames    = list(LibnameForSystem.values())


class PdfiumVer:
    
    # TODO consider namedtuple?
    V_KEYS = ("major", "minor", "build", "patch")
    
    # TODO consider cached property?
    @staticmethod
    @functools.lru_cache(maxsize=1)
    def get_latest():
        git_ls = run_cmd(["git", "ls-remote", f"{ReleaseRepo}.git"], cwd=None, capture=True)
        tag = git_ls.split("\t")[-1]
        return int( tag.split("/")[-1] )
    
    @staticmethod
    def to_full(v_short, origin):
        
        if origin == "pdfium-binaries":
            # NOTE(future:conda) we may need this info to pin pdfium-binaries
            info = url_request.urlopen(f"{ReleaseInfoURL}{v_short}").read().decode("utf-8")
            info = json.loads(info)
            title = info["name"]
            match = re.match(rf"PDFium (\d+.\d+.{v_short}.\d+)", title)
            v_string = match.group(1)
            v_parts = [int(v) for v in v_string.split(".")]
            v_short = int(v_short)
        elif origin == "sourcebuild":
            # For sourcebuild, we don't actually set the full version. Retrieving it from chromium is a bit complicated. Also note v_short may be a commit hash if building from an untagged commit.
            v_parts = (None, None, v_short, None)
        else:
            assert False
        
        v_info = dict(zip(PdfiumVer.V_KEYS, v_parts))
        assert v_info["build"] == v_short
        
        return v_info


# TODO Could consider adding a checksum to our JSON files as an barrier against corruption

def read_json(fp):
    with open(fp, "r") as buf:
        return json.load(buf)

def write_json(fp, data, indent=2):
    with open(fp, "w") as buf:
        return json.dump(data, buf, indent=indent)


def write_pdfium_info(dir, version, origin, flags=[]):
    # TODO(future) embed library search path for use with a custom ctypesgen loader
    info = dict(**PdfiumVer.to_full(version, origin), origin=origin, flags=flags)
    write_json(dir/VersionFN, info)


def parse_given_tag(full_tag):
    
    info = dict()
    
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
    
    # FIXME some duplication with src/pypdfium2/version.py
    
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
            print("Warning: Ignored post-tag desc. This should not happen in autorelease CI.")
    
    return tag


def plat_to_system(pl_name):
    if pl_name == PlatNames.sourcebuild:
        # FIXME If doing a sourcebuild on an unknown host system, this returns None, which will cause binary detection code to fail (we need to know the platform-specific binary name) - handle this downsteam with fallback value?
        return Host.system
    result = [s for s in BinarySystems if pl_name.startswith(s)]
    assert len(result) == 1
    return result[0]


# platform.libc_ver() currently returns an empty string for musl, so use the packaging module to confirm.
# See https://github.com/python/cpython/issues/87414 and https://github.com/pypa/packaging/blob/f13c298f0a623f3f7e01cc8395956b718d21503a/src/packaging/_musllinux.py#L32
# NOTE could consider packaging.tags.sys_tags() as a possible public-API alternative - see https://packaging.pypa.io/en/stable/tags.html#packaging.tags.sys_tags or https://stackoverflow.com/a/75172415/15547292

def _get_libc_info():
    
    name, ver = platform.libc_ver()
    if name.startswith("musl"):
        # try to be future proof in case libc_ver() gets musl support but uses "muslc" rather than just "musl"
        name = "musl"
    elif name == "":
        # TODO add test ensuring this continues to work
        import packaging._musllinux
        musl_ver = packaging._musllinux._get_musl_version(sys.executable)
        if musl_ver:
            name, ver = "musl", f"{musl_ver.major}.{musl_ver.minor}"
    
    return name, ver


class _host_platform:
    
    def __init__(self):
        
        # Get info about the host platform (OS and CPU)
        # For the machine name, the platform module just passes through info provided by the OS (e.g. the uname command on unix), so we can determine the relevant names from Python's source code, system specs or info available online (e.g. https://en.wikipedia.org/wiki/Uname)
        self._system_name = platform.system().lower()
        self._machine_name = platform.machine().lower()
        
        # If we are on Linux, check if we have glibc or musl
        self._libc_name, self._libc_ver = _get_libc_info()
        
        # TODO consider cached property for platform and system
        self.platform = self._get_platform()
        self.system = None
        if self.platform is not None:
            self.system = plat_to_system(self.platform)
    
    def __repr__(self):
        info = f"{self._system_name} {self._machine_name}"
        if self._system_name == "linux" and self._libc_name:
            info += f", {self._libc_name} {self._libc_ver}"
        return f"<Host: {info}>"
    
    def _is_plat(self, system, machine):
        return self._system_name.startswith(system) and self._machine_name.startswith(machine)
    
    def _get_platform(self):
        # some machine names are merely "qualified guesses", mistakes can't be fully excluded for platforms we don't have access to
        if self._is_plat("darwin", "x86_64"):
            return PlatNames.darwin_x64
        elif self._is_plat("darwin", "arm64"):
            return PlatNames.darwin_arm64
        elif self._is_plat("linux", "x86_64"):
            return PlatNames.linux_x64 if self._libc_name != "musl" else PlatNames.linux_musl_x64
        elif self._is_plat("linux", "i686"):
            return PlatNames.linux_x86 if self._libc_name != "musl" else PlatNames.linux_musl_x86
        elif self._is_plat("linux", "aarch64"):
            return PlatNames.linux_arm64 if self._libc_name != "musl" else PlatNames.linux_musl_arm64
        elif self._is_plat("linux", "armv7l"):
            return PlatNames.linux_arm32
        elif self._is_plat("windows", "amd64"):
            return PlatNames.windows_x64
        elif self._is_plat("windows", "arm64"):
            return PlatNames.windows_arm64
        elif self._is_plat("windows", "x86"):
            return PlatNames.windows_x86
        else:
            return None

Host = _host_platform()


def get_wheel_tag(pl_name):
    if pl_name == PlatNames.darwin_x64:
        # pdfium-binaries/steps/05-configure.sh defines `mac_deployment_target = "10.13.0"`
        return "macosx_10_13_x86_64"
    elif pl_name == PlatNames.darwin_arm64:
        # macOS 11 is the first version available on arm64
        return "macosx_11_0_arm64"
    # linux glibc requirement: see BUG(203) for discussion
    # TODO unify glibc/musl CPU translation
    elif pl_name == PlatNames.linux_x64:
        return "manylinux_2_17_x86_64"
    elif pl_name == PlatNames.linux_x86:
        return "manylinux_2_17_i686"
    elif pl_name == PlatNames.linux_arm64:
        return "manylinux_2_17_aarch64"
    elif pl_name == PlatNames.linux_arm32:
        return "manylinux_2_17_armv7l"
    elif pl_name == PlatNames.linux_musl_x64:
        return "musllinux_1_1_x86_64"
    elif pl_name == PlatNames.linux_musl_x86:
        return "musllinux_1_1_i686"
    elif pl_name == PlatNames.linux_musl_arm64:
        return "musllinux_1_1_aarch64"
    elif pl_name == PlatNames.windows_x64:
        return "win_amd64"
    elif pl_name == PlatNames.windows_arm64:
        return "win_arm64"
    elif pl_name == PlatNames.windows_x86:
        return "win32"
    elif pl_name == PlatNames.sourcebuild:
        # sysconfig.get_platform() may return universal2 on macOS. However, the binaries built here should be considered architecture-specific.
        # The reason why we don't simply do `if Host.platform: return get_wheel_tag(Host.platform) else ...` is that version info for pdfium-binaries does not have to match the sourcebuild host.
        # NOTE On Linux, this just returns f"linux_{arch}" (which is a valid wheel tag). Leave it as-is since we don't know the build's lowest compatible libc. The caller may re-tag using the wheel module's CLI.
        tag = sysconfig.get_platform().replace("-", "_").replace(".", "_")
        if tag.startswith("macosx") and tag.endswith("universal2"):
            tag = tag[:-len("universal2")] + Host._machine_name
        return tag
    else:
        raise ValueError(f"Unknown platform name {pl_name}")


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


def call_ctypesgen(target_dir, include_dir, pl_name, use_v8xfa=False, guard_symbols=False):
    
    # The commands below are tailored to our fork of ctypesgen, so make sure we have that
    # Import ctypesgen only in this function so it does not have to be available for other setup tasks
    import ctypesgen
    assert getattr(ctypesgen, "PYPDFIUM2_SPECIFIC", False)
    
    bindings = target_dir / BindingsFN
    
    args = ["ctypesgen", f"--strip-build-path={include_dir}", "--no-srcinfo", "--library", "pdfium", "--runtime-libdirs", "."]
    if pl_name == Host.platform:
        # assuming the binary already lies in target_dir
        args += ["--compile-libdirs", target_dir]
    else:
        args += ["--no-load-library"]
    if not guard_symbols:
        args += ["--no-symbol-guards"]
    if use_v8xfa:
        args += ["-D", "PDF_ENABLE_V8", "PDF_ENABLE_XFA"]
    if pl_name.startswith(SysNames.windows) and Host.system == SysNames.windows:
        args += ["-D", "_WIN32"]
    args += ["--headers"] + [h.name for h in sorted(include_dir.glob("*.h"))] + ["-o", bindings]
    
    run_cmd(args, cwd=include_dir)
    
    text = bindings.read_text()
    text = text.replace(str(include_dir), ".")
    text = text.replace(str(Path.home()), "~")
    bindings.write_text(text)


def clean_platfiles():
    
    deletables = [
        ProjectDir / "build",
        ModuleDir_Raw / BindingsFN,
        ModuleDir_Raw / VersionFN,
    ]
    deletables += [ModuleDir_Raw / fn for fn in MainLibnames]
    
    for fp in deletables:
        if fp.is_file():
            fp.unlink()
        elif fp.is_dir():
            shutil.rmtree(fp)


def get_platfiles(pl_name):
    system = plat_to_system(pl_name)
    platfiles = (
        DataDir / pl_name / BindingsFN,
        DataDir / pl_name / LibnameForSystem[system],
    )
    return platfiles


def emplace_platfiles(pl_name):
    
    pl_dir = DataDir / pl_name
    ver_file = pl_dir / VersionFN
    if not pl_dir.exists():
        raise RuntimeError(f"Missing platform directory {pl_name}")
    if not ver_file.exists():
        raise RuntimeError(f"Missing PDFium version file for {pl_name}")
    
    clean_platfiles()
    platfiles = get_platfiles(pl_name)
    shutil.copyfile(ver_file, ModuleDir_Raw/VersionFN)
    
    for fp in platfiles:
        if not fp.exists():
            raise RuntimeError(f"Platform file missing: {fp}")
        shutil.copy(fp, ModuleDir_Raw)
