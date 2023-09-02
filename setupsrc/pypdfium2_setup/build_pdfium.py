#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# NOTE Works on Linux/macOS/Windows (that is, at least on GitHub Actions)

import os
import sys
import shutil
import argparse
import urllib.request
from pathlib import Path, WindowsPath

sys.path.insert(0, str(Path(__file__).parents[1]))
# TODO? consider glob import or dotted access
from pypdfium2_setup.packaging_base import (
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


PatchDir       = SB_Dir / "patches"
DepotToolsDir  = SB_Dir / "depot_tools"
PDFiumDir      = SB_Dir / "pdfium"
PDFiumBuildDir = PDFiumDir / "out" / "Default"
OutputDir      = DataTree / PlatformNames.sourcebuild

PatchesMain = [
    (PatchDir/"shared_library.patch", PDFiumDir),
    (PatchDir/"public_headers.patch", PDFiumDir),
]
PatchesWindows = [
    (PatchDir/"win"/"pdfium.patch", PDFiumDir),
    (PatchDir/"win"/"build.patch", PDFiumDir/"build"),
]

DefaultConfig = {
    "is_debug": False,
    "treat_warnings_as_errors": False,
    "pdf_is_standalone": True,
    "pdf_enable_v8": False,
    "pdf_enable_xfa": False,
    "pdf_use_skia": False,
}

SyslibsConfig = {
    "use_system_freetype": True,
    "use_system_lcms2": True,
    "use_system_libjpeg": True,
    "use_system_libopenjpeg2": True,
    "use_system_libpng": True,
    "use_system_zlib": True,
    "use_system_libtiff": True,
    "clang_use_chrome_plugins": False,
}


if sys.platform.startswith("linux"):
    SyslibsConfig["use_custom_libcxx"] = False
    SyslibsConfig["use_sysroot"] = False
elif sys.platform.startswith("darwin"):
    DefaultConfig["mac_deployment_target"] = "10.13.0"
    SyslibsConfig["use_system_xcode"] = True


def dl_depottools(do_update):
    
    SB_Dir.mkdir(parents=True, exist_ok=True)
    
    is_update = True
    if DepotToolsDir.exists():
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
    
    os.environ["PATH"] += os.pathsep + str(DepotToolsDir)
    
    return is_update


def dl_pdfium(GClient, do_update, revision):
    
    is_sync = True
    
    if PDFiumDir.exists():
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
        run_cmd([GClient, "sync", "--revision", f"origin/{revision}", "--no-history", "--with_branch_heads"], cwd=SB_Dir)
    
    return is_sync


def _dl_unbundler():

    # Workaround: download missing tools for unbundle/replace_gn_files.py (syslibs build)

    tool_dir = PDFiumDir / "tools" / "generate_shim_headers"
    tool_file = tool_dir / "generate_shim_headers.py"
    tool_url = "https://raw.githubusercontent.com/chromium/chromium/main/tools/generate_shim_headers/generate_shim_headers.py"

    tool_dir.mkdir(parents=True, exist_ok=True)
    if not tool_file.exists():
        urllib.request.urlretrieve(tool_url, tool_file)


def get_pdfium_version():
    
    # FIXME awkward mix of local/remote git - this will fail to identify the tag if local and remote state do not match
    
    head_commit = run_cmd(["git", "rev-parse", "--short", "HEAD"], cwd=PDFiumDir, capture=True)
    refs_string = run_cmd(["git", "ls-remote", "--heads", PDFium_URL, "chromium/*"], cwd=None, capture=True)
    
    latest = refs_string.split("\n")[-1]
    tag_commit, ref = latest.split("\t")
    tag_commit = tag_commit[:7]
    tag = ref.split("/")[-1]
    
    print(f"Current head {head_commit}, latest tagged commit {tag_commit} ({tag})", file=sys.stderr)
    v_libpdfium = tag if head_commit == tag_commit else head_commit
    
    return v_libpdfium


def update_version(v_libpdfium):
    ver_file = OutputDir / VerStatusFileName
    ver_file.write_text( str(v_libpdfium) )


def _create_resources_rc(v_libpdfium):
    
    input_path = PatchDir / "win" / "resources.rc"
    output_path = PDFiumDir / "resources.rc"
    content = input_path.read_text()
    
    # NOTE RC does not seem to tolerate commit hash, so set a dummy version instead
    if not v_libpdfium.isnumeric():
        v_libpdfium = "1.0"
    
    content = content.replace("$VERSION_CSV", v_libpdfium.replace(".", ","))
    content = content.replace("$VERSION", v_libpdfium)
    output_path.write_text(content)


def _apply_patchset(patchset, check=True):
    for patch, cwd in patchset:
        run_cmd(["git", "apply", "--ignore-space-change", "--ignore-whitespace", "-v", patch], cwd=cwd, check=check)


def patch_pdfium(v_libpdfium):
    _apply_patchset(PatchesMain)
    if sys.platform.startswith("win32"):
        _apply_patchset(PatchesWindows)
        _create_resources_rc(v_libpdfium)


def configure(GN, config):
    PDFiumBuildDir.mkdir(parents=True, exist_ok=True)
    (PDFiumBuildDir / "args.gn").write_text(config)
    run_cmd([GN, "gen", PDFiumBuildDir], cwd=PDFiumDir)


def build(Ninja, target):
    run_cmd([Ninja, "-C", PDFiumBuildDir, target], cwd=PDFiumDir)


def find_lib(src_libname=None, directory=PDFiumBuildDir):
    
    if src_libname is not None:
        path = directory / src_libname
        if path.exists():
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
        raise RuntimeError(f"Not sure how pdfium artifact is called on platform '{sys.platform}'")
    
    libpath = directory / libname
    assert libpath.exists()
    
    return libpath


def pack(src_libpath, v_libpdfium, destname=None):
    
    # TODO remove existing binary/bindings, just to be safe
    
    if destname is None:
        destname = LibnameForSystem[Host.system]
    
    OutputDir.mkdir(parents=True, exist_ok=True)
    destpath = OutputDir / destname
    shutil.copy(src_libpath, destpath)
    
    update_version(v_libpdfium)
    
    include_dir = PDFiumDir / "public"
    call_ctypesgen(OutputDir, include_dir)


def get_tool(name):
    bin = DepotToolsDir / name
    if sys.platform.startswith("win32"):
        bin = bin.with_suffix(".bat")
    return bin


def serialise_config(config_dict):
    
    config_str = ""
    sep = ""
    
    for key, value in config_dict.items():
        config_str += sep + f"{key} = "
        if isinstance(value, bool):
            config_str += str(value).lower()
        elif isinstance(value, str):
            config_str += f'"{value}"'
        else:
            raise TypeError(f"Not sure how to serialise type {type(value).__name__}")
        sep = "\n"
    
    return config_str


def main(
        b_src_libname = None,
        b_dest_libname = None,
        b_update = False,
        b_revision = None,
        b_target = None,
        b_use_syslibs = False,
        b_win_sdk_dir = None,
    ):
    
    # NOTE defaults handled internally to avoid duplication with parse_args()
    
    if b_revision is None:
        b_revision = "main"
    if b_target is None:
        b_target = "pdfium"
    
    if sys.platform.startswith("win32"):
        if b_win_sdk_dir is None:
            b_win_sdk_dir = WindowsPath(R"C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64")
        assert b_win_sdk_dir.exists()
        os.environ["PATH"] += os.pathsep + str(b_win_sdk_dir)
        os.environ["DEPOT_TOOLS_WIN_TOOLCHAIN"] = "0"
    
    dl_depottools(b_update)
    
    GClient = get_tool("gclient")
    GN      = get_tool("gn")
    Ninja   = get_tool("ninja")
    
    pdfium_dl_done = dl_pdfium(GClient, b_update, b_revision)
    v_libpdfium = get_pdfium_version()
    
    if pdfium_dl_done:
        patch_pdfium(v_libpdfium)
    if b_use_syslibs:
        _dl_unbundler()

    if b_use_syslibs:
        run_cmd(["python3", "build/linux/unbundle/replace_gn_files.py", "--system-libraries", "icu"], cwd=PDFiumDir)
    
    config_dict = DefaultConfig.copy()
    if b_use_syslibs:
        config_dict.update(SyslibsConfig)
    config_str = serialise_config(config_dict)
    print(f"\nBuild configuration:\n{config_str}\n")
    
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
    parser.add_argument(
        "--use-syslibs", "-l",
        action = "store_true",
        help = "Use system libraries instead of those bundled with PDFium. Make sure that freetype, lcms2, libjpeg, libopenjpeg2, libpng, zlib and icuuc are installed, and that $PKG_CONFIG_PATH is set correctly.",
    )
    parser.add_argument(
        "--win-sdk-dir",
        type = WindowsPath,
        help = "Path to the Windows SDK (Windows only)",
    )
    
    return parser.parse_args(argv)


def main_cli(argv=sys.argv[1:]):
    return main( **{"b_"+k : v for k, v in vars( parse_args(argv) ).items()} )
    

if __name__ == "__main__":
    main_cli()
