#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Attempt to download and build PDFium from source. This may take very long.
# Only tested on Linux with glibc. Might not work on other platforms.

import os
import sys
import shutil
import argparse
import urllib.request
from os.path import join, abspath, dirname

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from pl_setup.packaging_base import (
    SB_Dir,
    Libnames,
    DataTree,
    VerNamespace,
    PlatformNames,
    run_cmd,
    call_ctypesgen,
    set_version,
)


PatchDir       = join(SB_Dir, "patches")
DepotToolsDir  = join(SB_Dir, "depot_tools")
PDFiumDir      = join(SB_Dir, "pdfium")
PDFiumBuildDir = join(PDFiumDir, "out", "Default")
OutputDir      = join(DataTree, PlatformNames.sourcebuild)

DepotTools_URL = "https://chromium.googlesource.com/chromium/tools/depot_tools.git"
PDFium_URL     = "https://pdfium.googlesource.com/pdfium.git"

DepotPatches = [
    (join(PatchDir, "depot_tools", "gclient_scm.patch"), DepotToolsDir),
]
PdfiumMainPatches = [
    (join(PatchDir, "pdfium", "public_headers.patch"), PDFiumDir),
    (join(PatchDir, "pdfium", "shared_library.patch"), PDFiumDir),
]
PdfiumWinPatches = [
    (join(PatchDir, "pdfium", "win", "pdfium.patch"), PDFiumDir),
    (join(PatchDir, "pdfium", "win", "build.patch"), join(PDFiumDir, "build")),
]

DefaultConfig = {
    "is_debug": False,
    "treat_warnings_as_errors": False,
    # "clang_use_chrome_plugins": False,
    "pdf_is_standalone": True,
    "pdf_enable_v8": False,
    "pdf_enable_xfa": False,
    "pdf_use_skia": False,
}
SyslibsConfig = {
    "use_system_freetype": True,
    "use_system_lcms2": True,
    # "use_system_libjpeg": True,
    "use_system_libopenjpeg2": True,
    "use_system_libpng": True,
    "use_system_zlib": True,
    "sysroot": "/",
}

if sys.platform.startswith("linux"):
    SyslibsConfig["use_custom_libcxx"] = False
elif sys.platform.startswith("darwin"):
    DefaultConfig["mac_deployment_target"] = "10.11.0"
    SyslibsConfig["use_system_xcode"] = True
elif sys.platform.startswith("win32"):
    DefaultConfig["pdf_use_win32_gdi"] = True

Git = shutil.which("git")


def dl_depottools(do_update):
    
    if not os.path.isdir(SB_Dir):
        os.makedirs(SB_Dir)
    
    is_update = True
    
    if os.path.isdir(DepotToolsDir):
        if do_update:
            print("DepotTools: Revert and update ...")
            run_cmd(["git", "reset", "--hard", "HEAD"], cwd=DepotToolsDir)
            run_cmd(["git", "pull", DepotTools_URL], cwd=DepotToolsDir)
        else:
            print("DepotTools: Using existing repository as-is.")
            is_update = False
    else:
        print("DepotTools: Download ...")
        run_cmd(["git", "clone", "--depth", "1", DepotTools_URL, DepotToolsDir], cwd=SB_Dir)
    
    os.environ["PATH"] += os.pathsep + DepotToolsDir
    
    return is_update


def _dl_unbundler():
    
    # Download missing tools for unbundle/replace_gn_files.py
    
    tool_url = "https://raw.githubusercontent.com/chromium/chromium/main/tools/generate_shim_headers/generate_shim_headers.py"
    tool_dir = join(PDFiumDir,"tools","generate_shim_headers")
    tool_file = join(tool_dir, "generate_shim_headers.py")
    
    if not os.path.isdir(tool_dir):
        os.makedirs(tool_dir)
    if not os.path.exists(tool_file):
        urllib.request.urlretrieve(tool_url, tool_file)


def dl_pdfium(do_update, revision, GClient):
    
    is_sync = True
    
    if os.path.isdir(PDFiumDir):
        if do_update:
            print("PDFium: Revert / Sync  ...")
            run_cmd([GClient, "revert"], cwd=SB_Dir)
        else:
            is_sync = False
            print("PDFium: Using existing repository as-is.")
    else:
        print("PDFium: Download ...")
        run_cmd([GClient, "config", "--unmanaged", PDFium_URL], cwd=SB_Dir)
    
    if is_sync:
        run_cmd([GClient, "sync", "--revision", "origin/%s" % revision, "--no-history", "--shallow"], cwd=SB_Dir)
        _dl_unbundler()
    
    return is_sync


def get_version_info():
    head_commit = run_cmd([Git, "rev-parse", "--short", "HEAD"], cwd=PDFiumDir, capture=True)
    refs_string = run_cmd([Git, "ls-remote", "--heads", PDFium_URL, "chromium/*"], cwd=None, capture=True)
    latest = refs_string.split("\n")[-1]
    tag_commit, ref = latest.split("\t")
    tag = ref.split("/")[-1]
    return head_commit, tag_commit[:7], tag


def update_version(head_commit, tag_commit, tag):
    
    is_sourcebuild  = VerNamespace["IS_SOURCEBUILD"]
    curr_libversion = VerNamespace["V_LIBPDFIUM"]
    
    print("Current head %s, latest tagged commit %s (%s)" % (head_commit, tag_commit, tag))
    if head_commit == tag_commit:
        new_libversion = tag
    else:
        new_libversion = head_commit
    
    if not is_sourcebuild:
        print("Switching from pre-built binaries to source build.")
        set_version("IS_SOURCEBUILD", True)
    if curr_libversion != new_libversion:
        set_version("V_LIBPDFIUM", new_libversion)


def _apply_patchset(patchset):
    for patch, cwd in patchset:
        run_cmd(["git", "apply", "-v", patch], cwd=cwd)

def patch_depottools():
    _apply_patchset(DepotPatches)

def patch_pdfium():
    _apply_patchset(PdfiumMainPatches)
    if sys.platform.startswith("win32"):
        _apply_patchset(PdfiumWinPatches)
        shutil.copy(join(PatchDir, "pdfium", "win", "resources.rc"), join(PDFiumDir, "resources.rc"))


def configure(config, GN):
    if not os.path.exists(PDFiumBuildDir):
        os.makedirs(PDFiumBuildDir)
    with open(join(PDFiumBuildDir, "args.gn"), "w") as args_handle:
        args_handle.write(config)
    run_cmd([GN, "gen", PDFiumBuildDir], cwd=PDFiumDir)


def build(Ninja, target):
    run_cmd([Ninja, "-C", PDFiumBuildDir, target], cwd=PDFiumDir)


def find_lib(srcname=None, directory=PDFiumBuildDir):
    
    if srcname is not None:
        path = join(PDFiumBuildDir, srcname)
        if os.path.isfile(path):
            return path
        else:
            print("Warning: The file of given srcname does not exist.", file=sys.stderr)
    
    libpath = None
    for lname in Libnames:
        path = join(directory, lname)
        if os.path.isfile(path):
            libpath = path
    
    if libpath is None:
        raise RuntimeError("Build artifact not found.")
    
    return libpath


def pack(src_libpath, destname=None):
    
    if os.path.isdir(OutputDir):
        shutil.rmtree(OutputDir)
    os.makedirs(OutputDir)
    
    if destname is None:
        destname = os.path.basename(src_libpath)
    
    destpath = join(OutputDir, destname)
    shutil.copy(src_libpath, destpath)
    
    include_dir = join(OutputDir, "include")
    shutil.copytree(join(PDFiumDir, "public"), include_dir)
    
    call_ctypesgen(OutputDir, include_dir)
    shutil.rmtree(include_dir)


def _get_tool(tool, win_append):
    exe = join(DepotToolsDir, tool)
    if sys.platform.startswith("win32"):
        exe += "." + win_append
    return exe


def _serialise_config(config_dict):
    
    config_str = ""
    sep = ""
    
    for key, value in config_dict.items():
        config_str += sep + "%s = " % key
        if isinstance(value, bool):
            config_str += str(value).lower()
        elif isinstance(value, str):
            config_str += '"%s"' % value
        else:
            raise TypeError("Not sure how to serialise type %s" % type(value))
        sep = "\n"
    
    return config_str


def main(
        b_srcname = None,
        b_destname = None,
        b_update = False,
        b_use_syslibs = False,
        b_revision = None,
        b_target = None,
    ):
    
    if b_revision is None:
        b_revision = "main"
    if b_target is None:
        b_target = "pdfium"
    # on Linux, rename the binary to `pdfium` to ensure it also works with older versions of ctypesgen
    if b_destname is None and sys.platform.startswith("linux"):
        b_destname = "pdfium"
    
    if sys.platform.startswith("win32"):
        os.environ["DEPOT_TOOLS_WIN_TOOLCHAIN"] = "0"
    
    depot_dl_done = dl_depottools(b_update)
    if depot_dl_done:
        patch_depottools()
    
    GClient = _get_tool("gclient", "bat")
    GN      = _get_tool("gn", "bat")
    Ninja   = _get_tool("ninja", "exe")
    
    pdfium_dl_done = dl_pdfium(b_update, b_revision, GClient)
    if pdfium_dl_done:
        patch_pdfium()
    
    update_version( *get_version_info() )
    
    config_dict = DefaultConfig.copy()
    if b_use_syslibs:
        config_dict.update(SyslibsConfig)
        run_cmd(["python3", "build/linux/unbundle/replace_gn_files.py", "--system-libraries", "icu"], cwd=PDFiumDir)
    config_str = _serialise_config(config_dict)
    print("\nBuild configuration:\n%s\n" % config_str)
    
    configure(config_str, GN)
    build(Ninja, b_target)
    libpath = find_lib(b_srcname)
    pack(libpath, b_destname)


def parse_args(argv):
    
    parser = argparse.ArgumentParser(
        description = "A script to automate building PDFium from source and generating bindings with ctypesgen.",
    )
    
    parser.add_argument(
        "--srcname", "-s",
        help = "Name of the generated PDFium binary file. This script tries to automatically find the binary, which should usually work. If it does not, however, this option may be used to explicitly provide the file name to look for.",
    )
    parser.add_argument(
        "--destname", "-d",
        help = "Rename the binary to a different filename.",
    )
    parser.add_argument(
        "--update", "-u",
        action = "store_true",
        help = "Update existing PDFium/DepotTools repositories, removing local changes.",
    )
    parser.add_argument(
        "--use-syslibs", "-l",
        action = "store_true",
        help = "Use system libraries instead of those bundled with PDFium. (Make sure that freetype, lcms2, libjpeg, libopenjpeg2, libpng, zlib and icuuc are installed, and that $PKG_CONFIG_PATH is set correctly (e. g. to `/usr/lib/x86_64-linux-gnu/pkgconfig`)",
    )
    parser.add_argument(
        "--revision", "-r",
        help = "PDFium revision to check out (defaults to main).",
    )
    parser.add_argument(
        "--target", "-t",
        help = "PDFium build target (defaults to `pdfium`). Use `pdfium_all` to also build tests."
    )
    
    return parser.parse_args(argv)


def main_cli(argv=sys.argv[1:]):
    args = parse_args(argv)
    return main(
        b_srcname = args.srcname,
        b_destname = args.destname,
        b_update = args.update,
        b_use_syslibs = args.use_syslibs,
        b_revision = args.revision,
        b_target = args.target,
    )
    

if __name__ == "__main__":
    main_cli()
