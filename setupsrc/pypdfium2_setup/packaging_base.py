# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# No external dependencies shall be imported in this file

import sys
import shutil
import platform
import sysconfig
import subprocess
from pathlib import Path

# TODO improve consistency of variable names; think about variables to move in/out

BinaryTargetVar      = "PDFIUM_PLATFORM"
BinaryTarget_None    = "none"
BinaryTarget_Auto    = "auto"
VersionTargetVar     = "PDFIUM_VERSION"
VersionTarget_Latest = "latest"
BindingsFileName     = "raw.py"  # NOTE if you rename this, delete the file `bindings/$VALUE`
VerStatusFileName    = ".pdfium_version.txt"
V8StatusFileName     = ".pdfium_is_v8.txt"
HomeDir              = Path.home()
SourceTree           = Path(__file__).parents[2]
DataTree             = SourceTree / "data"
SB_Dir               = SourceTree / "sourcebuild"
ModuleDir            = SourceTree / "src" / "pypdfium2"
VersionFile          = ModuleDir / "version.py"
Changelog            = SourceTree / "docs" / "devel" / "changelog.md"
ChangelogStaging     = SourceTree / "docs" / "devel" / "changelog_staging.md"
RepositoryURL        = "https://github.com/pypdfium2-team/pypdfium2"
PDFium_URL           = "https://pdfium.googlesource.com/pdfium"
DepotTools_URL       = "https://chromium.googlesource.com/chromium/tools/depot_tools.git"
ReleaseRepo          = "https://github.com/bblanchon/pdfium-binaries"
ReleaseURL           = ReleaseRepo + "/releases/download/chromium%2F"


# figure out whether our pypdfium2-specific fork of ctypesgen is installed
try:
    import ctypesgen
except ImportError:
    # ctypesgen not importable, might be installed on a different python version
    # in that case, we don't know if it's our fork, so assume mainline ctypesgen for compatibility
    CTYPESGEN_IS_FORK = False
else:
    CTYPESGEN_IS_FORK = getattr(ctypesgen, "PYPDFIUM2_SPECIFIC", False)


class SystemNames:
    linux   = "linux"
    darwin  = "darwin"
    windows = "windows"


class PlatformNames:
    # - Attribute names and values are expected to match
    # - Platform names are expected to start with the corresponding system name
    linux_x64      = SystemNames.linux   + "_x64"
    linux_x86      = SystemNames.linux   + "_x86"
    linux_arm64    = SystemNames.linux   + "_arm64"
    linux_arm32    = SystemNames.linux   + "_arm32"
    linux_musl_x64 = SystemNames.linux   + "_musl_x64"
    linux_musl_x86 = SystemNames.linux   + "_musl_x86"
    darwin_x64     = SystemNames.darwin  + "_x64"
    darwin_arm64   = SystemNames.darwin  + "_arm64"
    windows_x64    = SystemNames.windows + "_x64"
    windows_x86    = SystemNames.windows + "_x86"
    windows_arm64  = SystemNames.windows + "_arm64"
    sourcebuild    = "sourcebuild"


ReleaseNames = {
    PlatformNames.darwin_x64     : "mac-x64",
    PlatformNames.darwin_arm64   : "mac-arm64",
    PlatformNames.linux_x64      : "linux-x64",
    PlatformNames.linux_x86      : "linux-x86",
    PlatformNames.linux_arm64    : "linux-arm64",
    PlatformNames.linux_arm32    : "linux-arm",
    PlatformNames.linux_musl_x64 : "linux-musl-x64",
    PlatformNames.linux_musl_x86 : "linux-musl-x86",
    PlatformNames.windows_x64    : "win-x64",
    PlatformNames.windows_x86    : "win-x86",
    PlatformNames.windows_arm64  : "win-arm64",
}

# target names for pypdfium2/ctypesgen
LibnameForSystem = {
    SystemNames.linux:   "pdfium",
    SystemNames.darwin:  "pdfium.dylib",
    SystemNames.windows: "pdfium.dll",
}

BinaryPlatforms = list(ReleaseNames.keys())
BinarySystems   = list(LibnameForSystem.keys())
MainLibnames    = list(LibnameForSystem.values())

def plat_to_system(pl_name):
    if pl_name == PlatformNames.sourcebuild:
        # FIXME If doing a sourcebuild on an unknown host system, this returns None, which will cause binary detection code to fail (we need to know the platform-specific binary name) - handle this downsteam with fallback value?
        return Host.system
    result = [s for s in BinarySystems if pl_name.startswith(s)]
    assert len(result) == 1
    return result[0]


class _host_platform:
    
    def __init__(self):
        
        # Get information about the host platform (system and machine name)
        # For the machine name, the platform module just passes through information provided by the OS (The uname command on Unix, or an equivalent implementation on other systems like Windows), so we can determine the relevant names from Python's source code, system specs or information available online (e. g. https://en.wikipedia.org/wiki/Uname)
        # There is also sysconfig.get_platform() which we used before, but its behaviour did not fully match our needs (esp. on macOS)
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
            return PlatformNames.darwin_x64
        elif self._is_plat("darwin", "arm64"):
            return PlatformNames.darwin_arm64
        elif self._is_plat("linux", "x86_64"):
            return PlatformNames.linux_x64 if self._is_glibc else PlatformNames.linux_musl_x64
        elif self._is_plat("linux", "i686"):
            return PlatformNames.linux_x86 if self._is_glibc else PlatformNames.linux_musl_x86
        elif self._is_plat("linux", "armv7l"):
            return PlatformNames.linux_arm32
        elif self._is_plat("linux", "aarch64"):
            return PlatformNames.linux_arm64
        elif self._is_plat("windows", "amd64"):
            return PlatformNames.windows_x64
        elif self._is_plat("windows", "arm64"):
            return PlatformNames.windows_arm64
        elif self._is_plat("windows", "x86"):
            return PlatformNames.windows_x86
        else:
            return None


Host = _host_platform()


def get_wheel_tag(pl_name):
    if pl_name == PlatformNames.darwin_x64:
        # pdfium-binaries/steps/05-configure.sh defines `mac_deployment_target = "10.13.0"`
        return "macosx_10_13_x86_64"
    elif pl_name == PlatformNames.darwin_arm64:
        # macOS 11 is the first version available on arm64
        return "macosx_11_0_arm64"
    # linux glibc requirement: see BUG(203) for discussion
    elif pl_name == PlatformNames.linux_x64:
        return "manylinux_2_17_x86_64"
    elif pl_name == PlatformNames.linux_x86:
        return "manylinux_2_17_i686"
    elif pl_name == PlatformNames.linux_arm64:
        return "manylinux_2_17_aarch64"
    elif pl_name == PlatformNames.linux_arm32:
        return "manylinux_2_17_armv7l"
    elif pl_name == PlatformNames.linux_musl_x64:
        return "musllinux_1_1_x86_64"
    elif pl_name == PlatformNames.linux_musl_x86:
        return "musllinux_1_1_i686"
    elif pl_name == PlatformNames.windows_x64:
        return "win_amd64"
    elif pl_name == PlatformNames.windows_arm64:
        return "win_arm64"
    elif pl_name == PlatformNames.windows_x86:
        return "win32"
    elif pl_name == PlatformNames.sourcebuild:
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


def get_latest_version():
    git_ls = run_cmd(["git", "ls-remote", f"{ReleaseRepo}.git"], cwd=None, capture=True)
    tag = git_ls.split("\t")[-1]
    return int( tag.split("/")[-1] )


def call_ctypesgen(target_dir, include_dir, have_v8xfa=False):
    
    # see https://github.com/ctypesgen/ctypesgen/issues/160
    
    bindings = target_dir / BindingsFileName
    args = ["ctypesgen", "--library", "pdfium", "--runtime-libdir", ".", f"--strip-build-path={include_dir}"]
    if have_v8xfa:
        args += ["-D", "PDF_ENABLE_XFA", "-D", "PDF_ENABLE_V8"]
    if CTYPESGEN_IS_FORK:
        # extra arguments for our pypdfium2-specific fork of ctypesgen, not available in mainline ctypesgen (yet)
        args += ["--no-srcinfo"]
    args += [h.name for h in sorted(include_dir.glob("*.h"))] + ["-o", bindings]
    
    run_cmd(args, cwd=include_dir)
    
    text = bindings.read_text()
    text = text.replace(str(include_dir), ".")
    text = text.replace(str(HomeDir), "~")
    bindings.write_text(text)


def clean_platfiles():
    
    deletables = [
        SourceTree / "build",
        ModuleDir / BindingsFileName,
    ]
    deletables += [ModuleDir / fn for fn in MainLibnames]
    
    for fp in deletables:
        if fp.is_file():
            fp.unlink()
        elif fp.is_dir():
            shutil.rmtree(fp)


def get_platfiles(pl_name):
    system = plat_to_system(pl_name)
    platfiles = (
        DataTree / pl_name / BindingsFileName,
        DataTree / pl_name / LibnameForSystem[system],
    )
    return platfiles


def emplace_platfiles(pl_name):
    
    pl_dir = DataTree / pl_name
    if not pl_dir.exists():
        raise RuntimeError(f"Missing platform directory {pl_name} - you might have forgotten to run update_pdfium.py")
    
    ver_file = pl_dir / VerStatusFileName
    if not ver_file.exists():
        raise RuntimeError(f"Missing PDFium version file for {pl_name}")
    
    ver_changes = dict()
    ver_changes["V_LIBPDFIUM"] = ver_file.read_text().strip()
    ver_changes["V_BUILDNAME"] = "source" if pl_name == PlatformNames.sourcebuild else "pdfium-binaries"
    ver_changes["V_PDFIUM_IS_V8"] = (pl_dir / V8StatusFileName).exists()
    set_versions(ver_changes)
    
    clean_platfiles()
    platfiles = get_platfiles(pl_name)
    
    for fp in platfiles:
        if not fp.exists():
            raise RuntimeError(f"Platform file missing: {fp}")
        shutil.copy(fp, ModuleDir)


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
        
        # Beware: While this updates the VerNamespace entry itself, it will not update dependent entries, which may lead to inconsistent data. That is, no reliance can be placed upon the values of dynamic variables (V_PYPDFIUM2 !) after this method has been run. If you need the real value, VerNamespace needs to be re-created.
        VerNamespace[var] = new_val
    
    VersionFile.write_text(content)
    
    return True
