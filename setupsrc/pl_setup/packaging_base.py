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
    exists,
    abspath,
    dirname,
    expanduser,
)

# TODO improve consistency of variable names; think about variables to move in/out

HomeDir     = expanduser("~")
SourceTree  = dirname(dirname(dirname(abspath(__file__))))
DataTree    = join(SourceTree, "data")
SB_Dir      = join(SourceTree, "sourcebuild")
ModuleDir   = join(SourceTree, "src", "pypdfium2")
VersionFile = join(ModuleDir, "version.py")
Changelog   = join(SourceTree, "docs", "source", "changelog.md")
ChangelogStaging = join(SourceTree, "docs", "devel", "changelog_staging.md")
SetupTargetVar = "PYP_TARGET_PLATFORM"
SdistTarget    = "sdist"
RepositoryURL  = "https://github.com/pypdfium2-team/pypdfium2"
PDFium_URL     = "https://pdfium.googlesource.com/pdfium"
DepotTools_URL = "https://chromium.googlesource.com/chromium/tools/depot_tools.git"
ReleaseRepo    = "https://github.com/bblanchon/pdfium-binaries"
ReleaseURL     = ReleaseRepo + "/releases/download/chromium%2F"


Libnames = (
    "pdfium",
    "pdfium.dylib",
    "pdfium.dll",
    "libpdfium.so",
    "pdfium.so",
    "libpdfium",
    "libpdfium.dylib",
    "libpdfium.dll",
)


class PlatformNames:
    darwin_x64    = "darwin_x64"
    darwin_arm64  = "darwin_arm64"
    linux_x64     = "linux_x64"
    linux_x86     = "linux_x86"
    linux_arm64   = "linux_arm64"
    linux_arm32   = "linux_arm32"
    musllinux_x64 = "musllinux_x64"
    musllinux_x86 = "musllinux_x86"
    windows_x64   = "windows_x64"
    windows_x86   = "windows_x86"
    windows_arm64 = "windows_arm64"
    sourcebuild   = "sourcebuild"


ReleaseNames = {
    PlatformNames.darwin_x64    : "pdfium-mac-x64",
    PlatformNames.darwin_arm64  : "pdfium-mac-arm64",
    PlatformNames.linux_x64     : "pdfium-linux-x64",
    PlatformNames.linux_x86     : "pdfium-linux-x86",
    PlatformNames.linux_arm64   : "pdfium-linux-arm64",
    PlatformNames.linux_arm32   : "pdfium-linux-arm",
    PlatformNames.musllinux_x64 : "pdfium-linux-musl-x64",
    PlatformNames.musllinux_x86 : "pdfium-linux-musl-x86",
    PlatformNames.windows_x64   : "pdfium-win-x64",
    PlatformNames.windows_x86   : "pdfium-win-x86",
    PlatformNames.windows_arm64 : "pdfium-win-arm64",
}

BinaryPlatforms = list(ReleaseNames.keys())


class HostPlatform:
    
    def __init__(self):
        # `libc_ver()` currently returns an empty string on libc implementations other than glibc - hence, we assume musl if it's not glibc
        # FIXME is there some function to actually detect musl?
        self.plat_info = sysconfig.get_platform().lower().replace("-", "_").replace(".", "_")
        self.libc_info, self.is_glibc = None, None
        if self.plat_info.startswith("linux"):
            self.libc_info = platform.libc_ver()
            self.is_glibc = (self.libc_info[0] == "glibc")
    
    def _is_plat(self, start, end):
        return self.plat_info.startswith(start) and self.plat_info.endswith(end)
    
    def get_name(self):
        if self._is_plat("macosx", "arm64"):
            return PlatformNames.darwin_arm64
        elif self._is_plat("macosx", "x86_64"):
            return PlatformNames.darwin_x64
        elif self._is_plat("linux", "armv7l"):
            return PlatformNames.linux_arm32
        elif self._is_plat("linux", "aarch64"):
            return PlatformNames.linux_arm64
        elif self._is_plat("linux", "x86_64"):
            return PlatformNames.linux_x64 if self.is_glibc else PlatformNames.musllinux_x64
        elif self._is_plat("linux", "i686"):
            return PlatformNames.linux_x86 if self.is_glibc else PlatformNames.musllinux_x86
        elif self._is_plat("win", "arm64"):
            return PlatformNames.windows_arm64
        elif self._is_plat("win", "amd64"):
            return PlatformNames.windows_x64
        elif self._is_plat("win32", ""):
            return PlatformNames.windows_x86
        else:
            return None


def run_cmd(command, cwd, capture=False, **kwargs):
    
    print('%s ("%s")' % (command, cwd))
    if capture:
        kwargs.update( dict(stdout=subprocess.PIPE, stderr=subprocess.STDOUT) )
    
    comp_process = subprocess.run(command, cwd=cwd, **kwargs)
    if capture:
        return comp_process.stdout.decode("utf-8").strip()
    else:
        return comp_process


def get_latest_version(Git):
    git_ls = run_cmd([Git, "ls-remote", "%s.git" % ReleaseRepo], cwd=None, capture=True)
    tag = git_ls.split("\t")[-1]
    return int( tag.split("/")[-1] )


def call_ctypesgen(Ctypesgen, platform_dir, include_dir):
    
    bindings_file = join(platform_dir, "_pypdfium.py")
    
    ctypesgen_cmd = [Ctypesgen, "--library", "pdfium", "--strip-build-path", platform_dir, "-L", "."] + sorted(glob( join(include_dir, "*.h") )) + ["-o", bindings_file]
    run_cmd(ctypesgen_cmd, cwd=platform_dir)
    
    with open(bindings_file, "r") as file_reader:
        text = file_reader.read()
        text = text.replace(platform_dir, ".")
        text = text.replace(HomeDir, "~")
    
    with open(bindings_file, "w") as file_writer:
        file_writer.write(text)


def clean_artefacts():
    
    build_cache = join(SourceTree, "build")
    if exists(build_cache):
        shutil.rmtree(build_cache)
    
    deletable_files = [join(ModuleDir, n) for n in (*Libnames, "_pypdfium.py")]
    for file in deletable_files:
        if exists(file):
            os.remove(file)


def get_version_ns():
    ver_ns = {}
    with open(VersionFile, "r") as fh:
        exec(fh.read(), ver_ns)
    ver_ns = {k: v for k, v in ver_ns.items() if not k.startswith("_")}
    return ver_ns

VerNamespace = get_version_ns()


def set_version(variable, new_ver):
    
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
