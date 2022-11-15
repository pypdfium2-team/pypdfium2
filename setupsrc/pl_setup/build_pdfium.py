#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# NOTE Works on Linux/macOS/Windows (that is, at least on GitHub Actions)

import os
import sys
import shutil
import argparse
from os.path import join, abspath, dirname

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from pl_setup.packaging_base import (
    Host,
    SB_Dir,
    DataTree,
    PDFium_URL,
    DepotTools_URL,
    LibnameForSystem,
    VerStatusFileName,
    PlatformNames,
    run_cmd,
    call_ctypesgen,
)


PatchDir       = join(SB_Dir, "patches")
DepotToolsDir  = join(SB_Dir, "depot_tools")
PDFiumDir      = join(SB_Dir, "pdfium")
PDFiumBuildDir = join(PDFiumDir, "out", "Default")
OutputDir      = join(DataTree, PlatformNames.sourcebuild)

PdfiumMainPatches = [
    (join(PatchDir, "shared_library.patch"), PDFiumDir),
    (join(PatchDir, "public_headers.patch"), PDFiumDir),
]
PdfiumWinPatches = [
    (join(PatchDir, "win", "pdfium.patch"), PDFiumDir),
    (join(PatchDir, "win", "build.patch"), join(PDFiumDir, "build")),
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

if sys.platform.startswith("darwin"):
    DefaultConfig["mac_deployment_target"] = "10.13.0"


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


def dl_pdfium(GClient, do_update, revision):
    
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
        run_cmd([GClient, "config", "--custom-var", "checkout_configuration=minimal", "--unmanaged", PDFium_URL], cwd=SB_Dir)
    
    if is_sync:
        run_cmd([GClient, "sync", "--revision", "origin/%s" % revision, "--no-history", "--with_branch_heads"], cwd=SB_Dir)
    
    return is_sync


def get_pdfium_version():
    
    # FIXME awkward mix of local/remote git - this will fail to identify the tag if local and remote state do not match
    
    head_commit = run_cmd(["git", "rev-parse", "--short", "HEAD"], cwd=PDFiumDir, capture=True)
    refs_string = run_cmd(["git", "ls-remote", "--heads", PDFium_URL, "chromium/*"], cwd=None, capture=True)
    
    latest = refs_string.split("\n")[-1]
    tag_commit, ref = latest.split("\t")
    tag_commit = tag_commit[:7]
    tag = ref.split("/")[-1]
    
    print("Current head %s, latest tagged commit %s (%s)" % (head_commit, tag_commit, tag))
    
    if head_commit == tag_commit:
        v_libpdfium = tag
    else:
        v_libpdfium = head_commit
    
    return v_libpdfium


def update_version(v_libpdfium):
    ver_file = join(OutputDir, VerStatusFileName)
    with open(ver_file, "w") as fh:
        fh.write( str(v_libpdfium) )


def _create_resources_rc(v_libpdfium):
    
    input_path = join(PatchDir, "win", "resources.rc")
    output_path = join(PDFiumDir, "resources.rc")
    
    with open(input_path, "r") as fh:
        content = fh.read()
    
    # NOTE RC does not seem to tolerate commit hash, so set a dummy version instead
    if not v_libpdfium.isnumeric():
        v_libpdfium = "1.0"
    
    content = content.replace("$VERSION_CSV", v_libpdfium.replace(".", ","))
    content = content.replace("$VERSION", v_libpdfium)
    
    with open(output_path, "w") as fh:
        fh.write(content)


def _apply_patchset(patchset):
    for patch, cwd in patchset:
        run_cmd(["git", "apply", "--ignore-space-change", "--ignore-whitespace", "-v", patch], cwd=cwd)


def patch_pdfium(v_libpdfium):
    _apply_patchset(PdfiumMainPatches)
    if sys.platform.startswith("win32"):
        _apply_patchset(PdfiumWinPatches)
        _create_resources_rc(v_libpdfium)


def configure(GN, config):
    if not os.path.exists(PDFiumBuildDir):
        os.makedirs(PDFiumBuildDir)
    with open(join(PDFiumBuildDir, "args.gn"), "w") as args_handle:
        args_handle.write(config)
    run_cmd([GN, "gen", PDFiumBuildDir], cwd=PDFiumDir)


def build(Ninja, target):
    run_cmd([Ninja, "-C", PDFiumBuildDir, target], cwd=PDFiumDir)


def find_lib(src_libname=None, directory=PDFiumBuildDir):
    
    if src_libname is not None:
        path = join(PDFiumBuildDir, src_libname)
        if os.path.isfile(path):
            return path
        else:
            print("Warning: Binary not found under given name.", file=sys.stderr)
    
    if sys.platform.startswith("linux"):
        libname = "libpdfium.so"
    elif sys.platform.startswith("darwin"):
        libname = "libpdfium.dylib"
    elif sys.platform.startswith("win32"):
        libname = "pdfium.dll"
    else:
        # TODO implement fallback artifact detection
        raise RuntimeError("Not sure how pdfium artifact is called on platform '%s'" % (sys.platform, ))
    
    libpath = join(directory, libname)
    assert os.path.exists(libpath)
    
    return libpath


def pack(src_libpath, v_libpdfium, destname=None):
    
    # TODO remove existing binary/bindings, just to be safe
    
    if destname is None:
        destname = LibnameForSystem[Host.system]
    
    destpath = join(OutputDir, destname)
    shutil.copy(src_libpath, destpath)
    
    update_version(v_libpdfium)
    
    include_dir = join(PDFiumDir, "public")
    call_ctypesgen(OutputDir, include_dir)


def get_tool(tool, win_append):
    exe = join(DepotToolsDir, tool)
    if sys.platform.startswith("win32"):
        exe += "." + win_append
    return exe


def serialise_config(config_dict):
    
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
        b_src_libname = None,
        b_dest_libname = None,
        b_update = False,
        b_revision = None,
        b_target = None,
    ):
    
    if not os.path.exists(OutputDir):
        os.makedirs(OutputDir)
    
    if b_revision is None:
        b_revision = "main"
    if b_target is None:
        b_target = "pdfium"
    
    # TODO make windows sdk dir configurable
    if sys.platform.startswith("win32"):
        os.environ["DEPOT_TOOLS_WIN_TOOLCHAIN"] = "0"
        WindowsSDK_DIR = R"C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64"
        assert os.path.isdir(WindowsSDK_DIR)
        os.environ["PATH"] += os.pathsep + WindowsSDK_DIR
    
    dl_depottools(b_update)
    
    GClient = get_tool("gclient", "bat")
    GN      = get_tool("gn", "bat")
    Ninja   = get_tool("ninja", "exe")
    
    pdfium_dl_done = dl_pdfium(GClient, b_update, b_revision)
    v_libpdfium = get_pdfium_version()
    if pdfium_dl_done:
        patch_pdfium(v_libpdfium)
    
    config_dict = DefaultConfig.copy()
    config_str = serialise_config(config_dict)
    print("\nBuild configuration:\n%s\n" % config_str)
    
    configure(GN, config_str)
    build(Ninja, b_target)
    libpath = find_lib(b_src_libname)
    pack(libpath, v_libpdfium, b_dest_libname)


def parse_args(argv):
    
    parser = argparse.ArgumentParser(
        description = "A script to automate building PDFium from source and generating bindings with ctypesgen.",
    )
    
    parser.add_argument(
        "--src-libname",
        help = "Name of the generated PDFium binary file. This script tries to automatically find the binary, which should usually work. If it does not, however, this option may be used to explicitly provide the file name to look for.",
    )
    parser.add_argument(
        "--dest-libname",
        help = "Rename the binary. Must be a name recognised by packaging code.",
    )
    parser.add_argument(
        "--update", "-u",
        action = "store_true",
        help = "Update existing PDFium/DepotTools repositories, removing local changes.",
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
        b_src_libname  = args.src_libname,
        b_dest_libname = args.dest_libname,
        b_update   = args.update,
        b_revision = args.revision,
        b_target   = args.target,
    )
    

if __name__ == "__main__":
    main_cli()
