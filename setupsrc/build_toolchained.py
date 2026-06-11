#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import argparse
from pathlib import Path

# local
from base import *
from _build_helpers import *

SBDir = ProjectDir / "sbuild" / "toolchained"
DepotToolsDir  = SBDir / "depot_tools"
PDFiumDir      = SBDir / "pdfium"
PDFiumDir_build = PDFiumDir / "build"
PDFiumOutDir = PDFiumDir / "out" / "Default"

DEFAULT_MODE = Host.platform == PlatNames.linux_x64 or Host.system in (SysNames.windows, SysNames.darwin)
PORTABLE_MODE = not DEFAULT_MODE

# run `gn args --list out/Default/` for build config docs

DefaultConfig = {
    "use_glib": False,
    "use_siso": False,
    "is_debug": False,
    "treat_warnings_as_errors": False,
    "is_component_build": False,
    "pdf_is_standalone": True,
    "pdf_use_partition_alloc": False,
    "pdf_enable_v8": False,
    "pdf_enable_xfa": False,
    "pdf_use_skia": False,
}


def dl_depottools(do_update):
    
    mkdir(SBDir)
    
    if DepotToolsDir.exists():
        if do_update:
            log("DepotTools: Revert and update ...")
            run_cmd(["git", "reset", "--hard", "HEAD"], cwd=DepotToolsDir)
            run_cmd(["git", "pull", DepotToolsURL], cwd=DepotToolsDir)
        else:
            log("DepotTools: Using existing repository as-is.")
    else:
        log("DepotTools: Download ...")
        run_cmd(["git", "clone", "--depth", "1", DepotToolsURL, DepotToolsDir], cwd=SBDir)
    
    orig_path = os.environ["PATH"]
    env_prepend("PATH", str(DepotToolsDir), os.pathsep)
    
    return orig_path


def _get_tool_impl(name):
    bin = DepotToolsDir/name
    if sys.platform.startswith("win32"):
        bin = bin.with_suffix(".bat")
    return bin

def _get_gclient_cmd():
    if PORTABLE_MODE:
        return (sys.executable, DepotToolsDir/f"gclient.py")
    return (_get_tool_impl("gclient"), )

def dl_pdfium(do_update, revision, target_os, orig_path):
    
    gclient_cmd = _get_gclient_cmd()
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
        run_cmd([*gclient_cmd, "config", "--custom-var", "checkout_configuration=minimal", *extra_vars, "--unmanaged", PdfiumURL], cwd=SBDir, check=DEFAULT_MODE)
    
    if do_update:
        log("PDFium: download/sync ...")
        args = [*gclient_cmd, "sync"]
        if had_pdfium:
            args += ["-D", "--reset"]
        args += ["--revision", f"origin/{revision}", "--no-history", "--shallow"]
        run_cmd(args, cwd=SBDir, check=DEFAULT_MODE)
    
    if PORTABLE_MODE:
        # remove depot_tools from PATH after checkout phase, gn/ninja wrappers don't seem portable
        os.environ["PATH"] = orig_path
    
    return do_update


def _create_resources_rc(build_ver):
    input_path = PatchDir / "win" / "resources.rc"
    output_path = PDFiumDir / "resources.rc"
    content = input_path.read_text()
    content = content.replace("$VERSION_CSV", str(build_ver))
    content = content.replace("$VERSION", str(build_ver))
    output_path.write_text(content)

def patch_pdfium(build_ver, target_cpu, target_os, patch_clang):
    # TODO in the future, we might want to extract separate DLLs for the imaging libraries (e.g. libjpeg, libpng)
    shared_autopatches(PDFiumDir)
    if sys.platform.startswith("win32"):
        git_apply_patch(PatchDir/"win"/"use_resources_rc.patch", PDFiumDir)
        git_apply_patch(PatchDir/"win"/"build.patch", PDFiumDir_build)
        _create_resources_rc(build_ver)
        if Host._raw_machine == "arm64":
            git_apply_patch(PatchDir/"win"/"arm64_native.patch", PDFiumDir_build)
    if sys.platform.startswith("linux") and target_cpu == "ppc64":
        git_apply_patch(PatchDir/"ppc64_cross.patch", PDFiumDir)
    if target_os == "android":
        # without this patch, we end up with a tiny binary that has no symbols
        git_apply_patch(PatchDir/"android_cross.patch", PDFiumDir_build)
    if PORTABLE_MODE:
        git_apply_patch(PatchDir/"gcc_toolchain.patch", PDFiumDir_build)
        if patch_clang:
            git_apply_patch(PatchDir/"clang_22_compat.patch", PDFiumDir_build)
            git_apply_patch(PatchDir/"no_libclang_rt.patch", PDFiumDir_build)


def _get_tool(name):
    if PORTABLE_MODE:
        return name
    return _get_tool_impl(name)

def configure(config):
    mkdir(PDFiumOutDir)
    (PDFiumOutDir / "args.gn").write_text(config)
    gn = _get_tool("gn")
    run_cmd([gn, "gen", PDFiumOutDir], cwd=PDFiumDir)

def build(target):
    ninja = _get_tool("ninja")
    run_cmd([ninja, "-C", PDFiumOutDir, target], cwd=PDFiumDir)


def handle_portable_mode(config, use_sysroot, clang_path):
    
    patch_clang = False
    if not PORTABLE_MODE:
        return patch_clang
    
    # cf. https://pkg.go.dev/go.chromium.org/luci/vpython#readme-configuration
    os.environ["VPYTHON_BYPASS"] = "manually managed python not supported by chrome operations"
    
    if not PDFiumDir.exists():
        run_cmd([sys.executable, "-m", "pip", "install", "httplib2==0.22.0"], cwd=None)
        # TODO in install_buildtools(), check system GN version and install gn-dist if it is too old
        install_buildtools()
    
    config["clang_use_chrome_plugins"] = False
    if clang_path:
        clang_ver = get_clang_version(clang_path)
        patch_clang = clang_ver < 23
        config.update({
            "is_clang": True,  # default
            "clang_base_path": str(clang_path),  # without trailing slash
            "clang_version": clang_ver,
        })
    else:
        config.update({
            "is_clang": False,
            "use_custom_libcxx": False,
        })
        if use_sysroot:
            log("Warning: --use-sysroot with GCC / system libcxx. This may or may not work. If it fails, bring your own clang and pass --clang-path.")
    
    if not use_sysroot:
        config["use_sysroot"] = False
    
    return patch_clang


def handle_windows(win_sdk_dir):
    if not sys.platform.startswith("win32"):
        return
    if win_sdk_dir is None:
        # Current GH Actions windows-latest
        sdk_cpu = "arm64" if Host._raw_machine == "arm64" else "x64"
        win_sdk_dir = Path(fR"C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\{sdk_cpu}")
    assert win_sdk_dir.exists()
    env_append("PATH", str(win_sdk_dir), os.pathsep)  # ... prepend?
    os.environ["DEPOT_TOOLS_WIN_TOOLCHAIN"] = "0"


def handle_cross(config, target_cpu, target_os):
    
    # TODO compare target_cpu against host to determine whether it's actually cross
    # this is a bit difficult currently as we don't have a direct mapping between google and python-style CPU names
    is_cross = False
    
    if target_cpu:
        config["target_cpu"] = target_cpu
        is_cross = True  # assumed
        if sys.platform.startswith("linux"):
            if not target_os:
                sysroot_cpu = target_cpu
                if target_cpu == "ppc64":
                    sysroot_cpu = "ppc64le"
                run_cmd([sys.executable, "build/linux/sysroot_scripts/install-sysroot.py", "--arch", sysroot_cpu], cwd=PDFiumDir)
            if target_cpu == "ppc64":
                config["sysroot"] = "//build/linux/debian_bullseye_ppc64el-sysroot"
                config["use_sysroot"] = True
    
    if target_os:
        config["target_os"] = target_os
        if target_os == "android":
            config["default_min_sdk_version"] = 23
            config["use_mold"] = False
    
    return is_cross


def main(
        do_update    = False,
        build_ver    = None,
        build_target = None,
        win_sdk_dir  = None,
        target_cpu   = None,
        target_os    = None,
        use_sysroot  = None,
        clang_path   = None,
    ):
    
    # defaults handled internally to avoid duplication with parse_args()
    if target_cpu is None:
        if Host.platform == PlatNames.windows_arm64:
            target_cpu = "arm64"  # needed, even if native
    if build_target is None:
        build_target = "pdfium"
    if build_ver is None:
        build_ver = SBUILD_TOOLCHAINED_PIN
    
    v_full, pdfium_rev, chromium_rev = handle_sbuild_vers(build_ver)
    config = DefaultConfig.copy()
    patch_clang = handle_portable_mode(config, use_sysroot, clang_path)
    handle_windows(win_sdk_dir)
    
    orig_path = dl_depottools(do_update)
    did_pdfium_sync = dl_pdfium(do_update, pdfium_rev, target_os, orig_path)
    if did_pdfium_sync:
        patch_pdfium(build_ver, target_cpu, target_os, patch_clang)
    
    is_cross = handle_cross(config, target_cpu, target_os)
    config_str = serialize_gn_config(config)
    configure(config_str)
    build(build_target)
    
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
        default = (os.environ.get("PDFIUM_VER") or None),
        help = f"PDFium version to use. Either a literal version number, or 'main' to try the latest state. Defaults to the pinned version {SBUILD_TOOLCHAINED_PIN}, or $PDFIUM_VER if set.",
    )
    parser.add_argument(
        "--target", "-t",
        dest = "build_target",
        help = "PDFium build target (defaults to `pdfium`). Use `pdfium_all` to also build tests."
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
    parser.add_argument(
        "--use-sysroot",
        action = "store_true",
        help = "(PORTABLE_MODE only) Attempt to use a sysroot, on behalf of packaging, assuming a sysroot is available for the platform in question and has been automatically downloaded by gclient. This may or may not work with GCC / system libcxx. If it does not, bring your own clang and pass --clang-path.",
    )
    parser.add_argument(
        "--clang-path",
        type = lambda p: Path(p).expanduser().resolve(),
        help = "(PORTABLE_MODE only) Custom clang path. AOTW, clang >= 22 is required.",
    )
    
    return parser.parse_args(argv)


def main_cli(argv=sys.argv[1:]):
    args = parse_args(argv)
    return main(**vars(args))
    

if __name__ == "__main__":
    main_cli()
