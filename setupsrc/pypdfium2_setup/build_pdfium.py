#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# NOTE Works on Linux/macOS/Windows (that is, at least on GitHub Actions)

import os
import sys
import shutil
import argparse
import urllib.request as url_request
from pathlib import Path, WindowsPath

sys.path.insert(0, str(Path(__file__).parents[1]))
# TODO consider dotted access?
from pypdfium2_setup.packaging_base import *

SBDir = SourcebuildDir  # local alias for convenience
PatchDir       = SBDir / "patches"
DepotToolsDir  = SBDir / "depot_tools"
PDFiumDir      = SBDir / "pdfium"
PDFiumBuildDir = PDFiumDir / "out" / "Default"

PatchesMain = [
    (PatchDir/"shared_library.patch", PDFiumDir),
    (PatchDir/"public_headers.patch", PDFiumDir),
]
PatchesWindows = [
    (PatchDir/"win"/"pdfium.patch", PDFiumDir),
    (PatchDir/"win"/"build.patch", PDFiumDir/"build"),
]


# run `gn args out/Default/ --list` for build config docs

DefaultConfig = {
    "is_debug": False,
    "treat_warnings_as_errors": False,
    "pdf_is_standalone": True,
    "pdf_enable_v8": False,
    "pdf_enable_xfa": False,
    "pdf_use_skia": False,
    "use_allocator_shim": False,
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
    "pdf_use_partition_alloc": False,
    "use_sysroot": False,
}


if sys.platform.startswith("linux"):
    SyslibsConfig["use_custom_libcxx"] = False
if sys.platform.startswith("darwin"):
    DefaultConfig["mac_deployment_target"] = "10.13.0"
    SyslibsConfig["use_system_xcode"] = True


def dl_depottools(do_update):
    
    SBDir.mkdir(parents=True, exist_ok=True)
    
    is_update = True
    if DepotToolsDir.exists():
        if do_update:
            print("DepotTools: Revert and update ...")
            run_cmd(["git", "reset", "--hard", "HEAD"], cwd=DepotToolsDir)
            run_cmd(["git", "pull", DepotToolsURL], cwd=DepotToolsDir)
        else:
            print("DepotTools: Using existing repository as-is.")
            is_update = False
    else:
        print("DepotTools: Download ...")
        run_cmd(["git", "clone", "--depth", "1", DepotToolsURL, DepotToolsDir], cwd=SBDir)
    
    os.environ["PATH"] += os.pathsep + str(DepotToolsDir)
    
    return is_update


def dl_pdfium(GClient, do_update, revision):
    
    is_sync = True
    
    if PDFiumDir.exists():
        if do_update:
            print("PDFium: Revert / Sync  ...")
            run_cmd([GClient, "revert"], cwd=SBDir)
        else:
            is_sync = False
            print("PDFium: Using existing repository as-is.")
    else:
        print("PDFium: Download ...")
        run_cmd([GClient, "config", "--custom-var", "checkout_configuration=minimal", "--unmanaged", PdfiumURL], cwd=SBDir)
    
    if is_sync:
        # TODO consider passing -D ?
        run_cmd([GClient, "sync", "--revision", f"origin/{revision}", "--no-history", "--shallow"], cwd=SBDir)
        # quick & dirty fix to make a versioned commit available (pdfium gets tagged frequently, so this should be more than enough in practice)
        # FIXME avoid static number of commits, check out exactly up to latest versioned commit
        run_cmd(["git", "fetch", "--depth=100"], cwd=PDFiumDir)
    
    return is_sync


def _dl_unbundler():

    # Workaround: download missing tools for unbundle/replace_gn_files.py (to use ICU syslib)
    # TODO get this fixed upstream

    tool_dir = PDFiumDir / "tools" / "generate_shim_headers"
    tool_file = tool_dir / "generate_shim_headers.py"
    tool_url = "https://raw.githubusercontent.com/chromium/chromium/main/tools/generate_shim_headers/generate_shim_headers.py"

    if not tool_file.exists():
        tool_dir.mkdir(parents=True, exist_ok=True)
        url_request.urlretrieve(tool_url, tool_file)


def _walk_refs(log):
    for i, line in enumerate(log.split("\n")):
        for ref in line.split(", "):
            match = re.fullmatch(r"origin/chromium/(\d+)", ref.strip())
            if match:
                return int(match.group(1)), i
    assert False, "Failed to find versioned commit - log too small?"


def identify_pdfium():
    # we didn't manage to get git describe working reliably with chromium's branch heads and the awkward state the repo's in, so emulate git describe on our own
    # FIXME avoid static number of commits - need a better way to determine latest version and commit count diff
    log = run_cmd(["git", "log", "-100", "--pretty=%D"], cwd=PDFiumDir, capture=True)
    v_short, n_commits = _walk_refs(log)
    if n_commits:
        hash = "g" + run_cmd(["git", "rev-parse", "--short", "HEAD"], cwd=PDFiumDir, capture=True)
    else:
        hash = None
    v_info = dict(n_commits=n_commits, hash=hash)
    return v_short, v_info


def _create_resources_rc(pdfium_build):
    input_path = PatchDir / "win" / "resources.rc"
    output_path = PDFiumDir / "resources.rc"
    content = input_path.read_text()
    content = content.replace("$VERSION_CSV", str(pdfium_build))
    content = content.replace("$VERSION", str(pdfium_build))
    output_path.write_text(content)


def _apply_patchset(patchset, check=True):
    for patch, cwd in patchset:
        run_cmd(["git", "apply", "--ignore-space-change", "--ignore-whitespace", "-v", patch], cwd=cwd, check=check)


def patch_pdfium(pdfium_build):
    _apply_patchset(PatchesMain)
    if sys.platform.startswith("win32"):
        _apply_patchset(PatchesWindows)
        _create_resources_rc(pdfium_build)


def configure(GN, config):
    PDFiumBuildDir.mkdir(parents=True, exist_ok=True)
    (PDFiumBuildDir / "args.gn").write_text(config)
    run_cmd([GN, "gen", PDFiumBuildDir], cwd=PDFiumDir)


def build(Ninja, target):
    run_cmd([Ninja, "-C", PDFiumBuildDir, target], cwd=PDFiumDir)


def pack(v_short, v_post):
    
    dest_dir = DataDir / ExtPlats.sourcebuild
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    libname = LibnameForSystem[Host.system]
    shutil.copy(PDFiumBuildDir/libname, dest_dir/libname)
    write_pdfium_info(dest_dir, v_short, origin="sourcebuild", **v_post)
    
    # We want to use local headers instead of downloading with build_pdfium_bindings(), therefore call run_ctypesgen() directly
    # FIXME PDFIUM_BINDINGS=reference not honored
    run_ctypesgen(dest_dir, headers_dir=PDFiumDir/"public", compile_lds=[dest_dir])


def get_tool(name):
    bin = DepotToolsDir / name
    if sys.platform.startswith("win32"):
        bin = bin.with_suffix(".bat")
    return bin


def serialise_config(config_dict):
    
    parts = []
    
    for key, value in config_dict.items():
        p = f"{key} = "
        if isinstance(value, bool):
            p += str(value).lower()
        elif isinstance(value, str):
            p += f'"{value}"'
        else:
            raise TypeError(f"Not sure how to serialise type {type(value).__name__}")
        parts.append(p)
    
    return "\n".join(parts)


def main(
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
    v_short, v_post = identify_pdfium()
    print(f"Version {v_short} {v_post}", file=sys.stderr)
    
    if pdfium_dl_done:
        patch_pdfium(v_short)
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
    pack(v_short, v_post)


def parse_args(argv):
    
    parser = argparse.ArgumentParser(
        description = "A script to automate building PDFium from source and generating bindings with ctypesgen.",
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
