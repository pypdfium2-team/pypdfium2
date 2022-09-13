# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# No external dependencies shall be imported in this file

import os
import shutil
import platform
import sysconfig
import subprocess
from glob import glob
from os.path import (
    join,
    abspath,
    dirname,
    basename,
    expanduser,
)

# TODO improve consistency of variable names; think about variables to move in/out

BinaryTargetVar   = "PDFIUM_BINARY"
BinaryTarget_None = "none"
BinaryTarget_Auto = "auto"
BindingsFileName = "_pypdfium.py"
HomeDir     = expanduser("~")
SourceTree  = dirname(dirname(dirname(abspath(__file__))))
DataTree    = join(SourceTree, "data")
SB_Dir      = join(SourceTree, "sourcebuild")
ModuleDir   = join(SourceTree, "src", "pypdfium2")
VersionFile = join(ModuleDir, "version.py")
Changelog   = join(SourceTree, "docs", "source", "changelog.md")
ChangelogStaging = join(SourceTree, "docs", "devel", "changelog_staging.md")
RepositoryURL  = "https://github.com/pypdfium2-team/pypdfium2"
PDFium_URL     = "https://pdfium.googlesource.com/pdfium"
DepotTools_URL = "https://chromium.googlesource.com/chromium/tools/depot_tools.git"
ReleaseRepo    = "https://github.com/bblanchon/pdfium-binaries"
ReleaseURL     = ReleaseRepo + "/releases/download/chromium%2F"


class SystemNames:
    linux   = "linux"
    darwin  = "darwin"
    windows = "windows"


class PlatformNames:
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
    PlatformNames.darwin_x64     : "pdfium-mac-x64",
    PlatformNames.darwin_arm64   : "pdfium-mac-arm64",
    PlatformNames.linux_x64      : "pdfium-linux-x64",
    PlatformNames.linux_x86      : "pdfium-linux-x86",
    PlatformNames.linux_arm64    : "pdfium-linux-arm64",
    PlatformNames.linux_arm32    : "pdfium-linux-arm",
    PlatformNames.linux_musl_x64 : "pdfium-linux-musl-x64",
    PlatformNames.linux_musl_x86 : "pdfium-linux-musl-x86",
    PlatformNames.windows_x64    : "pdfium-win-x64",
    PlatformNames.windows_x86    : "pdfium-win-x86",
    PlatformNames.windows_arm64  : "pdfium-win-arm64",
}

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
        return Host.system
    result = [s for s in BinarySystems if pl_name.startswith(s)]
    assert len(result) == 1
    return result[0]


class _host_platform:
    
    def __init__(self):
        
        # `libc_ver()` currently returns an empty string on libc implementations other than glibc - hence, we assume musl if it's not glibc
        # FIXME is there some function to actually detect musl?
        self._plat_info = sysconfig.get_platform().lower().replace("-", "_").replace(".", "_")
        self._libc_info, self._is_glibc = None, None
        if self._plat_info.startswith("linux"):
            self._libc_info = platform.libc_ver()
            self._is_glibc = (self._libc_info[0] == "glibc")
        
        self.platform = self._get_platform()
        self.system = None
        if self.platform is not None:
            self.system = plat_to_system(self.platform)
    
    def _is_plat(self, start, end):
        return self._plat_info.startswith(start) and self._plat_info.endswith(end)
    
    def _get_platform(self):
        if self._is_plat("macosx", "arm64"):
            return PlatformNames.darwin_arm64
        elif self._is_plat("macosx", "x86_64"):
            return PlatformNames.darwin_x64
        elif self._is_plat("linux", "armv7l"):
            return PlatformNames.linux_arm32
        elif self._is_plat("linux", "aarch64"):
            return PlatformNames.linux_arm64
        elif self._is_plat("linux", "x86_64"):
            return PlatformNames.linux_x64 if self._is_glibc else PlatformNames.linux_musl_x64
        elif self._is_plat("linux", "i686"):
            return PlatformNames.linux_x86 if self._is_glibc else PlatformNames.linux_musl_x86
        elif self._is_plat("win", "arm64"):
            return PlatformNames.windows_arm64
        elif self._is_plat("win", "amd64"):
            return PlatformNames.windows_x64
        elif self._is_plat("win32", ""):
            return PlatformNames.windows_x86
        else:
            return None


Host = _host_platform()


def _get_linux_tag(arch):
    return "manylinux_2_17_%s.manylinux2014_%s" % (arch, arch)

def _get_musllinux_tag(arch):
    return "musllinux_1_2_%s" % (arch)


def _get_mac_tag(arch, *versions):
    
    assert len(versions) > 0
    
    template = "macosx_%s_%s"
    
    tag = ""
    sep = ""
    for v in versions:
        tag += sep + template % (v, arch)
        sep = "."
    
    return tag


def get_wheel_tag(pl_name):
    # pip>=20.3 now accepts macOS wheels tagged as 10_x on 11_x. Not sure what applies to 12_x.
    # Let's retain multi-version tagging for broader compatibility all the same.
    if pl_name == PlatformNames.darwin_x64:
        # pdfium-binaries/steps/05-configure.sh defines `mac_deployment_target = "10.13.0"`
        return _get_mac_tag("x86_64", "10_13", "11_0", "12_0")
    elif pl_name == PlatformNames.darwin_arm64:
        return _get_mac_tag("arm64", "11_0", "12_0")
    elif pl_name == PlatformNames.linux_x64:
        return _get_linux_tag("x86_64")
    elif pl_name == PlatformNames.linux_x86:
        return _get_linux_tag("i686")
    elif pl_name == PlatformNames.linux_arm64:
        return _get_linux_tag("aarch64")
    elif pl_name == PlatformNames.linux_arm32:
        return _get_linux_tag("armv7l")
    elif pl_name == PlatformNames.linux_musl_x64:
        return _get_musllinux_tag("x86_64")
    elif pl_name == PlatformNames.linux_musl_x86:
        return _get_musllinux_tag("i686")
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
        raise ValueError("Unknown platform name %s" % pl_name)


def run_cmd(command, cwd, capture=False, **kwargs):
    
    print('%s ("%s")' % (command, cwd))
    if capture:
        kwargs.update( dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT) )
    
    comp_process = subprocess.run(command, cwd=cwd, **kwargs)
    if capture:
        return comp_process.stdout.decode("utf-8").strip()
    else:
        return comp_process


def get_latest_version():
    git_ls = run_cmd(["git", "ls-remote", "%s.git" % ReleaseRepo], cwd=None, capture=True)
    tag = git_ls.split("\t")[-1]
    return int( tag.split("/")[-1] )


def call_ctypesgen(target_dir, include_dir):
    
    bindings = join(target_dir, BindingsFileName)
    
    ctypesgen_cmd = ["ctypesgen", "--library", "pdfium", "--strip-build-path", target_dir, "-L", "."] + sorted(glob( join(include_dir, "*.h") )) + ["-o", bindings]
    run_cmd(ctypesgen_cmd, cwd=target_dir)
    
    with open(bindings, "r") as file_reader:
        text = file_reader.read()
        text = text.replace(target_dir, ".")
        text = text.replace(HomeDir, "~")
    
    with open(bindings, "w") as file_writer:
        file_writer.write(text)


def clean_artefacts():
    
    deletables = [
        join(SourceTree, "build"),
        join(ModuleDir, BindingsFileName),
    ]
    deletables += [join(ModuleDir, fn) for fn in MainLibnames]
    
    for item in deletables:
        if not os.path.exists(item):
            continue
        if os.path.isfile(item):
            os.remove(item)
        elif os.path.isdir(item):
            shutil.rmtree(item)


def copy_platfiles(pl_name):
    
    # NOTE this will fail in case of sourcebuild with unknown host system
    system = plat_to_system(pl_name)
    binary_name = LibnameForSystem[system]
    
    platfiles = (
        join(DataTree, pl_name, BindingsFileName),
        join(DataTree, pl_name, binary_name)
    )
    
    for file in platfiles:
        if not os.path.exists(file):
            raise RuntimeError("Platform file missing: %s" % file)
        shutil.copy(file, join(ModuleDir, basename(file)))


def get_version_ns():
    ver_ns = {}
    with open(VersionFile, "r") as fh:
        exec(fh.read(), ver_ns)
    ver_ns = {k: v for k, v in ver_ns.items() if not k.startswith("_")}
    return ver_ns

VerNamespace = get_version_ns()


def set_version(variable, new_ver):
    
    # TODO(#136@geisserml) Change function to set multiple entries at once, to avoid inefficient repeated r/w of the version file.
    
    with open(VersionFile, "r") as fh:
        content = fh.read()
    
    if isinstance(new_ver, str):
        template = '%s = "%s"'
    else:
        template = '%s = %s'
    previous = template % (variable, VerNamespace[variable])
    updated = template % (variable, new_ver)
    
    print("'%s' -> '%s'" % (previous, updated))
    assert content.count(previous) == 1
    content = content.replace(previous, updated)
    VerNamespace[variable] = new_ver
    
    with open(VersionFile, "w") as fh:
        fh.write(content)
