#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# This script has been tested on Linux/macOS/Windows x86_64 on GH Actions CI
# However, it does not currently work on Linux aarch64 natively, since Google's toolchain doesn't seem to support that. Cross-compilation (by setting target_cpu in config) should work, though.

import os
import sys
import argparse
import urllib.request as url_request
from pathlib import Path, WindowsPath

sys.path.insert(0, str(Path(__file__).parents[1]))
from pypdfium2_setup.base import *

SBDir = ProjectDir / "sbuild" / "toolchained"
DepotToolsDir  = SBDir / "depot_tools"
PDFiumDir      = SBDir / "pdfium"
PDFiumBuildDir = PDFiumDir / "out" / "Default"


# run `gn args out/Default/ --list` for build config docs

DefaultConfig = {
    "is_debug": False,
    "treat_warnings_as_errors": False,
    "pdf_is_standalone": True,
    "pdf_enable_v8": False,
    "pdf_enable_xfa": False,
    "pdf_use_skia": False,
    # "use_allocator_shim": False,
    "pdf_use_partition_alloc": False,
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
    "use_sysroot": False,
}


if sys.platform.startswith("linux"):
    SyslibsConfig["use_custom_libcxx"] = False
if sys.platform.startswith("darwin"):
    DefaultConfig["mac_deployment_target"] = "10.13.0"
    SyslibsConfig["use_system_xcode"] = True


def dl_depottools(do_update):
    
    mkdir(SBDir)
    
    is_update = True
    if DepotToolsDir.exists():
        if do_update:
            log("DepotTools: Revert and update ...")
            run_cmd(["git", "reset", "--hard", "HEAD"], cwd=DepotToolsDir)
            run_cmd(["git", "pull", DepotToolsURL], cwd=DepotToolsDir)
        else:
            log("DepotTools: Using existing repository as-is.")
            is_update = False
    else:
        log("DepotTools: Download ...")
        run_cmd(["git", "clone", "--depth", "1", DepotToolsURL, DepotToolsDir], cwd=SBDir)
    
    os.environ["PATH"] = str(DepotToolsDir) + os.pathsep + os.environ["PATH"]
    
    return is_update


def dl_pdfium(GClient, do_update, revision):
    
    if not PDFiumDir.exists():
        log("PDFium: Download ...")
        do_update = True
        run_cmd([GClient, "config", "--custom-var", "checkout_configuration=minimal", "--unmanaged", PdfiumURL], cwd=SBDir)
    
    if do_update:
        run_cmd([GClient, "sync", "-D", "--reset", "--revision", f"origin/{revision}", "--no-history", "--shallow"], cwd=SBDir)
        # quick & dirty fix to make a versioned commit available (pdfium gets tagged frequently, so this should be more than enough in practice)
        # FIXME want to avoid static number of commits, and instead check out exactly up to latest versioned commit
        run_cmd(["git", "fetch", "--depth=100"], cwd=PDFiumDir)
        run_cmd(["git", "fetch", "--depth=100"], cwd=PDFiumDir)
    
    return do_update


def _dl_unbundler():

    # Workaround: download missing tool to unbundle ICU
    # TODO get this added to upstream pdfium, or use downloader code from build_native.py ?

    tool_dir = PDFiumDir / "tools" / "generate_shim_headers"
    tool_file = tool_dir / "generate_shim_headers.py"
    tool_url = "https://raw.githubusercontent.com/chromium/chromium/main/tools/generate_shim_headers/generate_shim_headers.py"

    if not tool_file.exists():
        mkdir(tool_dir)
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
    # FIXME want to avoid static number of commits - need a better way to determine latest version and commit count diff
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


def patch_pdfium(pdfium_build):
    git_apply_patch(PatchDir/"shared_library.patch", PDFiumDir)
    git_apply_patch(PatchDir/"public_headers.patch", PDFiumDir)
    if sys.platform.startswith("win32"):
        git_apply_patch(PatchDir/"win"/"build.patch", PDFiumDir/"build")
        _create_resources_rc(pdfium_build)


def configure(GN, config):
    mkdir(PDFiumBuildDir)
    (PDFiumBuildDir / "args.gn").write_text(config)
    run_cmd([GN, "gen", PDFiumBuildDir], cwd=PDFiumDir)


def build(Ninja, target):
    run_cmd([Ninja, "-C", PDFiumBuildDir, target], cwd=PDFiumDir)


def get_tool(name):
    bin = DepotToolsDir / name
    if sys.platform.startswith("win32"):
        bin = bin.with_suffix(".bat")
    return bin


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
    
    did_pdfium_sync = dl_pdfium(GClient, b_update, b_revision)
    v_short, v_post = identify_pdfium()
    log(f"Version {v_short} {v_post}")
    
    if did_pdfium_sync:
        patch_pdfium(v_short)
    
    config_dict = DefaultConfig.copy()
    if b_use_syslibs:
        _dl_unbundler()
        # alternatively, we could just copy build/linux/unbundle/icu.gn manually
        run_cmd(["python3", "build/linux/unbundle/replace_gn_files.py", "--system-libraries", "icu"], cwd=PDFiumDir)
        config_dict.update(SyslibsConfig)
    
    config_str = serialise_gn_config(config_dict)
    log(f"\nBuild configuration:\n{config_str}\n")
    
    configure(GN, config_str)
    build(Ninja, b_target)
    pack_sourcebuild(PDFiumDir, PDFiumBuildDir, v_short, **v_post, is_short_ver=True)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description = "Build PDFium from source using Google's toolchain.",
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
