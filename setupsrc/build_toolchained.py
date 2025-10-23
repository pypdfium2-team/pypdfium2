#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# This script has been tested on Linux/macOS/Windows x86_64 on GH Actions CI
# However, it does not currently work on Linux aarch64 natively, since Google's toolchain doesn't seem to support that. Cross-compilation (by setting target_cpu in config) should work, though.

import os
import sys
import argparse
from pathlib import Path

from base import *  # local

SBDir = ProjectDir / "sbuild" / "toolchained"
DepotToolsDir  = SBDir / "depot_tools"
PDFiumDir      = SBDir / "pdfium"
PDFiumOutDir = PDFiumDir / "out" / "Default"


# run `gn args --list out/Default/` for build config docs

DefaultConfig = {
    "is_debug": False,
    "treat_warnings_as_errors": False,
    "use_glib": False,
    "is_component_build": False,
    "pdf_is_standalone": True,
    "pdf_use_partition_alloc": False,
    "pdf_enable_v8": False,
    "pdf_enable_xfa": False,
    "pdf_use_skia": False,
}

SyslibsConfig = {
    "use_sysroot": False,
    "clang_use_chrome_plugins": False,
    "use_system_freetype": True,
    "use_system_lcms2": True,
    "use_system_libjpeg": True,
    "use_system_libopenjpeg2": True,
    "use_system_libpng": True,
    "use_system_zlib": True,
    "use_system_libtiff": True,
}

if sys.platform.startswith("darwin"):
    DefaultConfig["mac_deployment_target"] = "11.0.0"


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


def dl_pdfium(GClient, do_update, revision, target_os):
    
    had_pdfium = PDFiumDir.exists()
    if not had_pdfium or (target_os and do_update):
        log("PDFium: configure ...")
        do_update = True
        extra_vars = []
        if target_os == "android":
            # PDFium DEPS file says:
            # > By default, don't check out android. Will be overridden by gclient variables.
            # > TODO(crbug.com/875037): Remove this once the bug in gclient is fixed.
            extra_vars += ["--custom-var", "checkout_android=True"]
        run_cmd([GClient, "config", "--custom-var", "checkout_configuration=minimal", *extra_vars, "--unmanaged", PdfiumURL], cwd=SBDir)
    
    if do_update:
        log("PDFium: download/sync ...")
        args = [GClient, "sync"]
        if had_pdfium:
            args += ["-D", "--reset"]
        args += ["--revision", f"origin/{revision}", "--no-history", "--shallow"]
        run_cmd(args, cwd=SBDir)
    
    return do_update


def _create_resources_rc(build_ver):
    input_path = PatchDir / "win" / "resources.rc"
    output_path = PDFiumDir / "resources.rc"
    content = input_path.read_text()
    content = content.replace("$VERSION_CSV", str(build_ver))
    content = content.replace("$VERSION", str(build_ver))
    output_path.write_text(content)

def patch_pdfium(build_ver, target_os):
    # TODO
    # - use autopatch from build_native?
    # - in the future, we might want to extract separate DLLs for the imaging libraries (e.g. libjpeg, libpng)
    git_apply_patch(PatchDir/"single_lib.patch", PDFiumDir)
    git_apply_patch(PatchDir/"public_headers.patch", PDFiumDir)
    if sys.platform.startswith("win32"):
        git_apply_patch(PatchDir/"win"/"use_resources_rc.patch", PDFiumDir)
        git_apply_patch(PatchDir/"win"/"build.patch", PDFiumDir/"build")
        _create_resources_rc(build_ver)
    if target_os == "android":
        # without this patch, we end up with a tiny binary that has no symbols
        git_apply_patch(PatchDir/"android_crossbuild.patch", PDFiumDir/"build")


def get_tool(name):
    bin = DepotToolsDir / name
    if sys.platform.startswith("win32"):
        bin = bin.with_suffix(".bat")
    return bin

def configure(GN, config):
    mkdir(PDFiumOutDir)
    (PDFiumOutDir / "args.gn").write_text(config)
    run_cmd([GN, "gen", PDFiumOutDir], cwd=PDFiumDir)

def build(Ninja, target):
    run_cmd([Ninja, "-C", PDFiumOutDir, target], cwd=PDFiumDir)


def main(
        do_update    = False,
        build_ver    = None,
        build_target = None,
        use_syslibs  = False,
        win_sdk_dir  = None,
        target_cpu   = None,
        target_os    = None,
    ):
    
    # NOTE defaults handled internally to avoid duplication with parse_args()
    
    if build_target is None:
        build_target = "pdfium"
    if build_ver is None:
        build_ver = SBUILD_TOOLCHAINED_PIN
    
    v_full, pdfium_rev, chromium_rev = handle_sbuild_vers(build_ver)
    
    if sys.platform.startswith("win32"):
        if win_sdk_dir is None:
            # Current GH Actions windows-latest
            win_sdk_dir = Path(R"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64")
        assert win_sdk_dir.exists()
        os.environ["PATH"] += os.pathsep + str(win_sdk_dir)
        os.environ["DEPOT_TOOLS_WIN_TOOLCHAIN"] = "0"
    
    dl_depottools(do_update)
    
    GClient = get_tool("gclient")
    GN      = get_tool("gn")
    Ninja   = get_tool("ninja")
    
    did_pdfium_sync = dl_pdfium(GClient, do_update, pdfium_rev, target_os)
    
    if did_pdfium_sync:
        patch_pdfium(build_ver, target_os)
    if use_syslibs:
        assert not IGNORE_FULLVER
        get_shimheaders_tool(PDFiumDir, rev=chromium_rev)
        # alternatively, we could just copy build/linux/unbundle/icu.gn manually
        run_cmd([sys.executable, "build/linux/unbundle/replace_gn_files.py", "--system-libraries", "icu"], cwd=PDFiumDir)
    
    config_dict = DefaultConfig.copy()
    if use_syslibs:
        config_dict.update(SyslibsConfig)
    
    # TODO compare target_cpu against host to determine whether it's actually cross
    # this is a bit difficult currently as we don't have a direct mapping between google and python-style CPU names
    is_cross = False
    if target_cpu:
        config_dict["target_cpu"] = target_cpu
        is_cross = True  # assumed
        if is_cross and Host.system == SysNames.linux and not target_os:
            run_cmd([sys.executable, "build/linux/sysroot_scripts/install-sysroot.py", "--arch", target_cpu], cwd=PDFiumDir)
    if target_os:
        config_dict["target_os"] = target_os
        if target_os == "android":
            config_dict["default_min_sdk_version"] = 21
    
    config_str = serialize_gn_config(config_dict)
    configure(GN, config_str)
    build(Ninja, build_target)
    
    return pack_sourcebuild(PDFiumDir, PDFiumOutDir, "toolchained", v_full, build_ver, load_lib=(not is_cross))


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description = "Build PDFium from source using Google's toolchain.",
    )
    parser.add_argument(
        "--update", "-u",
        dest = "do_update",
        action = "store_true",
        help = "Update existing PDFium/DepotTools repositories, removing local changes.",
    )
    parser.add_argument(
        "--version", "-v",
        dest = "build_ver",
        help = f"PDFium version to use. Currently defaults to {SBUILD_TOOLCHAINED_PIN!r}. Pass 'main' to try the latest state.",
    )
    parser.add_argument(
        "--target", "-t",
        dest = "build_target",
        help = "PDFium build target (defaults to `pdfium`). Use `pdfium_all` to also build tests."
    )
    parser.add_argument(
        "--use-syslibs", "-l",
        action = "store_true",
        help = "Use system libraries instead of those bundled with PDFium. Make sure that freetype, lcms2, libjpeg, libopenjpeg2, libpng, zlib and icuuc are installed, and that $PKG_CONFIG_PATH is set correctly.",
    )
    parser.add_argument(
        "--win-sdk-dir",
        type = lambda p: Path(p).resolve(),
        help = "Path to the Windows SDK (Windows only)",
    )
    parser.add_argument(
        "--target-cpu",
        help = "The target CPU architecture. This sets the corresponding GN config var. Platform specific pre-requisites may apply, such as GCC multilib on Linux.",
    )
    parser.add_argument(
        "--target-os",
        help = "The target operating system, similar to --target-cpu. This is intended for compiling the mobile platforms (e.g. Android) from a desktop device. Note, this script has some issues with rebuilds - you may need to pass --update so that new patches can be applied."
    )
    return parser.parse_args(argv)


def main_cli(argv=sys.argv[1:]):
    args = parse_args(argv)
    return main(**vars(args))
    

if __name__ == "__main__":
    main_cli()
