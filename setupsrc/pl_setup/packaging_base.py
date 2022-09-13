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


# TODO(#136@geisserml) Internalise into build script. Replace with something that only includes the names that may land in platform folders.
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
    elif pl_name == PlatformNames.musllinux_x64:
        return _get_musllinux_tag("x86_64")
    elif pl_name == PlatformNames.musllinux_x86:
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


def call_ctypesgen(platform_dir, include_dir):
    
    bindings = join(platform_dir, BindingsFileName)
    
    ctypesgen_cmd = ["ctypesgen", "--library", "pdfium", "--strip-build-path", platform_dir, "-L", "."] + sorted(glob( join(include_dir, "*.h") )) + ["-o", bindings]
    run_cmd(ctypesgen_cmd, cwd=platform_dir)
    
    with open(bindings, "r") as file_reader:
        text = file_reader.read()
        text = text.replace(platform_dir, ".")
        text = text.replace(HomeDir, "~")
    
    with open(bindings, "w") as file_writer:
        file_writer.write(text)


def clean_artefacts():
    
    # TODO(#136@geisserml) Improve robustness.
    
    build_cache = join(SourceTree, "build")
    if exists(build_cache):
        shutil.rmtree(build_cache)
    
    deletable_files = [join(ModuleDir, n) for n in (*Libnames, BindingsFileName)]
    for file in deletable_files:
        if exists(file):
            os.remove(file)


def copy_platfiles(pl_name):
    
    # TODO(#136@geisserml) Improve robustness. Explicitly get the relevant files instead of globbing the directory.
    
    files = [f for f in glob(join(DataTree, pl_name, '*')) if os.path.isfile(f)]
    assert len(files) == 2
    
    for src_path in files:
        dest_path = join(ModuleDir, basename(src_path))
        shutil.copy(src_path, dest_path)


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
