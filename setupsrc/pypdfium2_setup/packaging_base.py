# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# No external dependencies shall be imported in this file
# TODO improve consistency of variable names; think about variables to move in/out

import re
import sys
import json
import shutil
import platform
import sysconfig
import subprocess
from pathlib import Path
import urllib.request as url_request

# TODO(apibreak) consider renaming PDFIUM_PLATFORM to PDFIUM_BINARY ?
PlatSpec_EnvVar  = "PDFIUM_PLATFORM"
PlatSpec_VerSep  = ":"
PlatSpec_V8Sym   = "-v8"
PlatTarget_None  = "none"  # sdist
PlatTarget_Auto  = "auto"  # host
VerTarget_Latest = "latest"

ModulesSpec_EnvVar = "PYPDFIUM_MODULES"
ModuleRaw          = "raw"
ModuleHelpers      = "helpers"
ModulesSpec_Dict   = {ModuleRaw: "pypdfium2_raw", ModuleHelpers: "pypdfium2"}
ModulesAll         = list(ModulesSpec_Dict.keys())

VerStatusFN = ".pdfium_version.txt"
V8StatusFN  = ".pdfium_is_v8.txt"
# NOTE if renaming BindingsFN, also rename `bindings/$FILE`
BindingsFN  = "bindings.py"

ProjectDir        = Path(__file__).parents[2]
ModuleDir_Raw     = ProjectDir / "src" / "pypdfium2_raw"
ModuleDir_Helpers = ProjectDir / "src" / "pypdfium2"
VersionFile       = ModuleDir_Helpers / "version.py"
DataDir           = ProjectDir / "data"
RefBindingsFile   = ProjectDir / "bindings" / BindingsFN
Changelog         = ProjectDir / "docs" / "devel" / "changelog.md"
ChangelogStaging  = ProjectDir / "docs" / "devel" / "changelog_staging.md"
SourcebuildDir    = ProjectDir / "sourcebuild"

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


class PlatNames:
    # - Attribute names and values are expected to match
    # - Platform names are expected to start with the corresponding system name
    linux_x64      = SysNames.linux   + "_x64"
    linux_x86      = SysNames.linux   + "_x86"
    linux_arm64    = SysNames.linux   + "_arm64"
    linux_arm32    = SysNames.linux   + "_arm32"
    linux_musl_x64 = SysNames.linux   + "_musl_x64"
    linux_musl_x86 = SysNames.linux   + "_musl_x86"
    darwin_x64     = SysNames.darwin  + "_x64"
    darwin_arm64   = SysNames.darwin  + "_arm64"
    windows_x64    = SysNames.windows + "_x64"
    windows_x86    = SysNames.windows + "_x86"
    windows_arm64  = SysNames.windows + "_arm64"
    sourcebuild    = "sourcebuild"


ReleaseNames = {
    PlatNames.darwin_x64     : "mac-x64",
    PlatNames.darwin_arm64   : "mac-arm64",
    PlatNames.linux_x64      : "linux-x64",
    PlatNames.linux_x86      : "linux-x86",
    PlatNames.linux_arm64    : "linux-arm64",
    PlatNames.linux_arm32    : "linux-arm",
    PlatNames.linux_musl_x64 : "linux-musl-x64",
    PlatNames.linux_musl_x86 : "linux-musl-x86",
    PlatNames.windows_x64    : "win-x64",
    PlatNames.windows_x86    : "win-x86",
    PlatNames.windows_arm64  : "win-arm64",
}

LibnameForSystem = {
    SysNames.linux:   "libpdfium.so",
    SysNames.darwin:  "libpdfium.dylib",
    SysNames.windows: "pdfium.dll",
}

BinaryPlatforms = list(ReleaseNames.keys())
BinarySystems   = list(LibnameForSystem.keys())
MainLibnames    = list(LibnameForSystem.values())

def plat_to_system(pl_name):
    if pl_name == PlatNames.sourcebuild:
        # FIXME If doing a sourcebuild on an unknown host system, this returns None, which will cause binary detection code to fail (we need to know the platform-specific binary name) - handle this downsteam with fallback value?
        return Host.system
    result = [s for s in BinarySystems if pl_name.startswith(s)]
    assert len(result) == 1
    return result[0]


class _host_platform:
    
    def __init__(self):
        
        # Get information about the host platform (system and machine name)
        # For the machine name, the platform module just passes through information provided by the OS (The uname command on Unix, or an equivalent implementation on other systems like Windows), so we can determine the relevant names from Python's source code, system specs or information available online (e. g. https://en.wikipedia.org/wiki/Uname)
        self._system_name = platform.system().lower()
        self._machine_name = platform.machine().lower()
        
        # https://github.com/python/cpython/issues/87414
        # `libc_ver()` currently returns an empty string on libc implementations other than glibc - hence, we assume musl if it's not glibc
        # TODO find some function to actually detect musl
        # See this for possible solutions: https://stackoverflow.com/questions/72272168/how-to-determine-which-libc-implementation-the-host-system-uses
        self._libc_info = None
        self._is_glibc = None
        if self._system_name == "linux":
            self._libc_info = platform.libc_ver()
            self._is_glibc = self._libc_info[0].startswith("glibc")
        
        self.platform = self._get_platform()
        self.system = None
        if self.platform is not None:
            self.system = plat_to_system(self.platform)
    
    def _is_plat(self, system, machine):
        return self._system_name.startswith(system) and self._machine_name.startswith(machine)
    
    def _get_platform(self):
        
        if self._system_name == "linux":
            assert self._is_glibc is not None
        
        # some machine names are merely "qualified guesses", mistakes can't be fully excluded for platforms we don't have access to
        if self._is_plat("darwin", "x86_64"):
            return PlatNames.darwin_x64
        elif self._is_plat("darwin", "arm64"):
            return PlatNames.darwin_arm64
        elif self._is_plat("linux", "x86_64"):
            return PlatNames.linux_x64 if self._is_glibc else PlatNames.linux_musl_x64
        elif self._is_plat("linux", "i686"):
            return PlatNames.linux_x86 if self._is_glibc else PlatNames.linux_musl_x86
        elif self._is_plat("linux", "armv7l"):
            return PlatNames.linux_arm32
        elif self._is_plat("linux", "aarch64"):
            return PlatNames.linux_arm64
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
    elif pl_name == PlatNames.windows_x64:
        return "win_amd64"
    elif pl_name == PlatNames.windows_arm64:
        return "win_arm64"
    elif pl_name == PlatNames.windows_x86:
        return "win32"
    elif pl_name == PlatNames.sourcebuild:
        tag = sysconfig.get_platform()
        for char in ("-", "."):
            tag = tag.replace(char, "_")
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


def get_version_ns():
    ver_ns = {}
    exec(VersionFile.read_text(), ver_ns)
    ver_ns = {k: v for k, v in ver_ns.items() if not k.startswith("_")}
    return ver_ns

VerNamespace = get_version_ns()


def set_versions(ver_changes):
    
    if len(ver_changes) == 0:
        return False
    skip = {var for var, value in ver_changes.items() if value == VerNamespace[var]}
    if len(skip) == len(ver_changes):
        return False
    
    content = VersionFile.read_text()
    
    for var, new_val in ver_changes.items():
        
        if var in skip:
            continue
        
        # this does not work universally - only one notation per type is supported, and switches between str and non-str types don't work
        # FIXME see if we can restructure this code for improved flexibility
        if isinstance(new_val, str):
            template = '%s = "%s"'
        else:
            template = '%s = %s'
        previous = template % (var, VerNamespace[var])
        updated = template % (var, new_val)
        
        print(f"'{previous}' -> '{updated}'")
        assert content.count(previous) == 1
        content = content.replace(previous, updated)
        
        # Beware: While this updates the VerNamespace entry itself, it will not update dependent entries, which may lead to inconsistent data. That is, dynamic values like V_PYPDFIUM2 cannot be relied on after this method has been run. If you need the actual current value, VerNamespace needs to be re-created.
        VerNamespace[var] = new_val
    
    VersionFile.write_text(content)
    
    return True


def get_latest_version():
    git_ls = run_cmd(["git", "ls-remote", f"{ReleaseRepo}.git"], cwd=None, capture=True)
    tag = git_ls.split("\t")[-1]
    return int( tag.split("/")[-1] )


def get_full_version(v_short):
    info = url_request.urlopen(f"{ReleaseInfoURL}{v_short}").read().decode("utf-8")
    info = json.loads(info)
    title = info["name"]
    match = re.match(rf"PDFium (\d+.\d+.{v_short}.\d+)", title)
    return match.group(1)


def read_version_file(path):
    ver_info = path.read_text().strip().split("\n")
    if len(ver_info) == 1:
        ver_info.append("")
    assert len(ver_info) == 2
    return tuple(ver_info)


def purge_pdfium_versions():
    set_versions(dict(
        V_LIBPDFIUM = "unknown",
        V_LIBPDFIUM_FULL = "",
        V_BUILDNAME = "unknown",
        V_PDFIUM_IS_V8 = None,
    ))


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
    if not pl_dir.exists():
        raise RuntimeError(f"Missing platform directory {pl_name}")
    
    ver_file = pl_dir / VerStatusFN
    if not ver_file.exists():
        raise RuntimeError(f"Missing PDFium version file for {pl_name}")
    
    ver_changes = dict()
    ver_changes["V_LIBPDFIUM"], ver_changes["V_LIBPDFIUM_FULL"] = read_version_file(ver_file)
    ver_changes["V_BUILDNAME"] = "source" if pl_name == PlatNames.sourcebuild else "pdfium-binaries"
    ver_changes["V_PDFIUM_IS_V8"] = (pl_dir / V8StatusFN).exists()
    set_versions(ver_changes)
    
    clean_platfiles()
    platfiles = get_platfiles(pl_name)
    
    for fp in platfiles:
        if not fp.exists():
            raise RuntimeError(f"Platform file missing: {fp}")
        shutil.copy(fp, ModuleDir_Raw)


def get_changelog_staging(flush=False):
    
    content = ChangelogStaging.read_text()
    pos = content.index("\n", content.index("# Changelog")) + 1
    header = content[:pos].strip() + "\n"
    devel_msg = content[pos:].strip()
    if devel_msg:
        devel_msg += "\n"
    
    if flush:
        ChangelogStaging.write_text(header)
    
    return devel_msg
