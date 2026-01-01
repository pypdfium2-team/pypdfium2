#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause
# Related work: https://github.com/tiran/libpdfium and https://aur.archlinux.org/packages/libpdfium-nojs

import re
import os
import sys
import shutil
import argparse
from enum import Enum
from pathlib import Path

from base import *  # local

PDFIUM_URL = "https://pdfium.googlesource.com/pdfium"
_CR_PREFIX = "https://chromium.googlesource.com/"
DEPS_URLS = dict(
    build      = _CR_PREFIX + "chromium/src/build",
    abseil     = _CR_PREFIX + "chromium/src/third_party/abseil-cpp",
    fast_float = _CR_PREFIX + "external/github.com/fastfloat/fast_float",
    catapult   = _CR_PREFIX + "catapult",  # android
    # vendorable dependencies
    icu         = _CR_PREFIX + "chromium/deps/icu",  # cibuildwheel
    buildtools  = _CR_PREFIX + "chromium/src/buildtools",
    libcxx      = _CR_PREFIX + "external/github.com/llvm/llvm-project/libcxx",
    libcxxabi   = _CR_PREFIX + "external/github.com/llvm/llvm-project/libcxxabi",
    llvm_libc   = _CR_PREFIX + "external/github.com/llvm/llvm-project/libc",
    freetype    = _CR_PREFIX + "chromium/src/third_party/freetype2",
    jpeg_turbo  = _CR_PREFIX + "chromium/deps/libjpeg_turbo",
    nasm_source = _CR_PREFIX + "chromium/deps/nasm",
    libpng      = _CR_PREFIX + "chromium/src/third_party/libpng",
    zlib        = _CR_PREFIX + "chromium/src/third_party/zlib",
    # unittests
    gtest      = _CR_PREFIX + "external/github.com/google/googletest",
    test_fonts = _CR_PREFIX + "chromium/src/third_party/test_fonts",
)
SOURCES_DIR = ProjectDir / "sbuild" / "native"
PDFIUM_DIR = SOURCES_DIR / "pdfium"
PDFIUM_DIR_build = PDFIUM_DIR / "build"
PDFIUM_3RDPARTY = PDFIUM_DIR / "third_party"

Compiler = Enum("Compiler", "gcc clang")

DefaultConfig = {
    "is_debug": False,
    "use_glib": False,
    "use_remoteexec": False,
    "treat_warnings_as_errors": False,
    "clang_use_chrome_plugins": False,
    "is_component_build": False,
    "pdf_is_standalone": True,
    "pdf_enable_v8": False,
    "pdf_enable_xfa": False,
    "pdf_use_skia": False,
    "pdf_use_partition_alloc": False,
    "use_sysroot": False,
}

IS_ANDROID = Host.system == SysNames.android
if IS_ANDROID:
    DefaultConfig.update({
        "sysroot": str(Host.usr.parent),
        "current_os": "android",
        "target_os": "android",
    })
    del DefaultConfig["use_sysroot"]
    # On Android, it seems that the build system's CPU type statically defaults to "arm", but we want this script to be host-adaptive (plus, "arm64" is the more likely candidate).
    # TODO(future) refactor platform constants from base.py so we can access abstracted OS/CPU separately through sub-attributes
    AndroidCPUMap = {
        "aarch64": "arm64",
        "armv7l":  "arm",
        "x86_64":  "x64",
        "i686":    "x86",
    }
    raw_cpu = Host._raw_machine
    if raw_cpu in AndroidCPUMap:
        cpu = AndroidCPUMap[raw_cpu]
        DefaultConfig.update({
            "current_cpu": cpu,
            "target_cpu": cpu,
        })
    else:
        log(f"Warning: Unknown Android CPU {raw_cpu}")


def _get_repo(url, rev, target_dir, reset=False, depth=1):
    
    if target_dir.exists():
        if reset:
            log(f"Resetting {target_dir.name} as per --reset option.")
            run_cmd(["git", "reset", "--hard"], cwd=target_dir)
            return True
        else:
            return False
    
    if callable(rev):
        rev = rev()  # resolve deferred
    
    git_clone_rev(url, rev, target_dir)
    
    return True


DEPS_RE = r"\s*'{key}': '(\w+)'"

class _DeferredInfo:
    
    def __init__(self, deps_fields):
        self.deps_fields = deps_fields
    
    @cached_property  # included from base.py
    def deps(self):
        # TODO get a proper parser for the DEPS file format?
        deps_content = (PDFIUM_DIR/"DEPS").read_text()
        result = {}
        for field in self.deps_fields:
            field_re = DEPS_RE.format(key=f"{field}_revision")
            match = re.search(field_re, deps_content)
            assert match, f"Could not find {field!r} in DEPS file"
            result[field] = match.group(1)
        log(f"Found DEPS revisions:\n{result}")
        return result


def handle_deps(config, vendor_deps, with_tests):
    
    deps_fields = ["build", "abseil", "fast_float"]
    if IS_ANDROID:
        deps_fields.append("catapult")
    
    if "libc++" in vendor_deps:
        deps_fields += ("buildtools", "libcxx", "libcxxabi", "llvm_libc")
    else:
        config["use_custom_libcxx"] = False
        config["use_libcxx_modules"] = False
    
    if "icu" in vendor_deps:
        deps_fields.append("icu")
    
    if "freetype" in vendor_deps:
        deps_fields.append("freetype")
    else:
        config["use_system_freetype"] = True
        config["pdf_bundle_freetype"] = False
    
    if "libjpeg" in vendor_deps:
        deps_fields += ("jpeg_turbo", "nasm_source")
    else:
        config["use_system_libjpeg"] = True
    
    if "libpng" in vendor_deps:
        deps_fields.append("libpng")
    else:
        config["use_system_libpng"] = True
    
    if "zlib" in vendor_deps:
        deps_fields.append("zlib")
    else:
        config["use_system_zlib"] = True
    
    if "lcms2" not in vendor_deps:
        config["use_system_lcms2"] = True
    if "openjpeg" not in vendor_deps:
        config["use_system_libopenjpeg2"] = True
    if "libtiff" not in vendor_deps:
        config["use_system_libtiff"] = True
    
    if with_tests:
        deps_fields += ("gtest", "test_fonts")
    
    return _DeferredInfo(deps_fields)

VendorableDeps = ("libc++", "icu", "freetype", "libjpeg", "libpng", "zlib", "lcms2", "openjpeg", "libtiff")


def _fetch_dep(info, name, target_dir, reset=False):
    # parse out DEPS revisions only when we actually need them
    return _get_repo(DEPS_URLS[name], lambda: info.deps[name], target_dir, reset=reset)


def get_sources(deps_info, short_ver, with_tests, compiler, clang_ver, clang_path, no_libclang_rt, reset, vendor_deps, compat):
    
    assert not IGNORE_FULLVER
    full_ver, pdfium_rev, chromium_rev = handle_sbuild_vers(short_ver)
    
    # pass through reset only for the repositories we actually patch
    do_patches = _get_repo(PDFIUM_URL, pdfium_rev, PDFIUM_DIR, reset=reset)
    if do_patches:
        shared_autopatches(PDFIUM_DIR)
        autopatch(
            PDFIUM_DIR/"testing"/"BUILD.gn",
            r'(\s*)("//third_party/test_fonts")', r"\1# \2",
            is_regex=True, exp_count=1,
        )
        if compat and not vendor_deps.issuperset(("openjpeg", "freetype")):
            # compatibility patch for older system libraries from container
            git_apply_patch(PatchDir/"legacy_libs_compat.patch", cwd=PDFIUM_DIR)
        if sys.byteorder == "big":
            git_apply_patch(PatchDir/"bigendian.patch", cwd=PDFIUM_DIR)
            if with_tests:
                git_apply_patch(PatchDir/"bigendian_test.patch", cwd=PDFIUM_DIR)
    
    do_patches = _fetch_dep(deps_info, "build", PDFIUM_DIR_build, reset=reset)
    if do_patches:
        # legacy_gn.patch: Work around error about path_exists() being undefined. This happens with older versions of GN.
        # Recent GN binaries can be obtained from https://chrome-infra-packages.appspot.com/p/gn/gn
        # Note that merely calling depot_tools `gn` is not sufficient, as it is only a wrapper script looking for vendored GN in the target repository, and if not present (as in this case), falls back to system GN.
        git_apply_patch(PatchDir/"legacy_gn.patch", cwd=PDFIUM_DIR_build)
        if IS_ANDROID:
            # fix linkage step
            git_apply_patch(PatchDir/"android_build.patch", cwd=PDFIUM_DIR_build)
        if compiler is Compiler.gcc:
            # https://crbug.com/402282789
            git_apply_patch(PatchDir/"ffp_contract.patch", cwd=PDFIUM_DIR_build)
        elif compiler is Compiler.clang:
            # https://crbug.com/410883044
            if "libc++" not in vendor_deps:
                git_apply_patch(PatchDir/"system_libcxx_with_clang.patch", cwd=PDFIUM_DIR_build)
            if clang_ver < 21:  # guessed
                git_apply_patch(PatchDir/"avoid_new_clang_flags.patch", cwd=PDFIUM_DIR_build)
            # TODO should we handle other OSes here?
            # see also https://groups.google.com/g/llvm-dev/c/k3q_ATl-K_0/m/MjEb6gsCCAAJ
            lld_path = clang_path/"bin"/"ld.lld"
            autopatch(
                PDFIUM_DIR_build/"config"/"compiler"/"BUILD.gn",
                'ldflags += [ "-fuse-ld=lld" ]',
                f'ldflags += [ "-fuse-ld={lld_path}" ]',
                is_regex=False, exp_count=1,
            )
            if no_libclang_rt:
                git_apply_patch(PatchDir/"no_libclang_rt.patch", cwd=PDFIUM_DIR_build)
        # Create an empty gclient config
        (PDFIUM_DIR_build/"config"/"gclient_args.gni").touch(exist_ok=True)
    
    do_patches = _fetch_dep(deps_info, "abseil", PDFIUM_3RDPARTY/"abseil-cpp", reset=reset)
    if do_patches and (Host._raw_machine, Host._libc_name) == ("ppc64le", "musl"):
        git_apply_patch(PatchDir/"abseil_ppc64le_musl.patch", cwd=PDFIUM_3RDPARTY/"abseil-cpp")
    
    _fetch_dep(deps_info, "fast_float", PDFIUM_3RDPARTY/"fast_float"/"src")
    if IS_ANDROID:
        _fetch_dep(deps_info, "catapult", PDFIUM_3RDPARTY/"catapult")
    
    if "libc++" in vendor_deps:
        _fetch_dep(deps_info, "buildtools", PDFIUM_DIR/"buildtools")
        _fetch_dep(deps_info, "libcxx", PDFIUM_3RDPARTY/"libc++"/"src")
        _fetch_dep(deps_info, "libcxxabi", PDFIUM_3RDPARTY/"libc++abi"/"src")
        _fetch_dep(deps_info, "llvm_libc", PDFIUM_3RDPARTY/"llvm-libc"/"src")
    
    if "icu" in vendor_deps:
        _fetch_dep(deps_info, "icu", PDFIUM_3RDPARTY/"icu")
    else:
        # unbundle (alternatively, we could call build/linux/unbundle/replace_gn_files.py --system-libraries icu)
        (PDFIUM_3RDPARTY/"icu").mkdir(exist_ok=True)
        shutil.copyfile(
            PDFIUM_DIR_build/"linux"/"unbundle"/"icu.gn",
            PDFIUM_3RDPARTY/"icu"/"BUILD.gn"
        )
    
    if "freetype" in vendor_deps:
        _fetch_dep(deps_info, "freetype", PDFIUM_3RDPARTY/"freetype"/"src")
    if "libjpeg" in vendor_deps:
        _fetch_dep(deps_info, "jpeg_turbo", PDFIUM_3RDPARTY/"libjpeg_turbo")
        _fetch_dep(deps_info, "nasm_source", PDFIUM_3RDPARTY/"nasm")
    if "libpng" in vendor_deps:
        _fetch_dep(deps_info, "libpng", PDFIUM_3RDPARTY/"libpng")
    if "zlib" in vendor_deps:
        _fetch_dep(deps_info, "zlib", PDFIUM_3RDPARTY/"zlib")
    
    if with_tests:
        _fetch_dep(deps_info, "gtest", PDFIUM_3RDPARTY/"googletest"/"src")
        _fetch_dep(deps_info, "test_fonts", PDFIUM_3RDPARTY/"test_fonts")
    
    get_shimheaders_tool(PDFIUM_DIR, rev=chromium_rev)
    
    return full_ver


def _get_clang_ver(clang_path):
    from packaging.version import Version
    output = run_cmd([str(clang_path/"bin"/"clang"), "--version"], capture=True, cwd=None)
    log(output)
    version = re.search(r"version ([\d\.]+)", output).group(1)
    version = Version(version).major
    log(f"Determined clang version {version!r}")
    return version

def setup_compiler(config, compiler, clang_ver, clang_path):
    if compiler is Compiler.gcc:
        config["is_clang"] = False
    elif compiler is Compiler.clang:
        assert clang_path, "Clang path must be set"
        config.update({
            "is_clang": True,
            "clang_base_path": str(clang_path),  # without trailing slash
            "clang_version": clang_ver,
        })
    else:
        assert False, f"Unhandled compiler {compiler}"


def build(build_dir, config_dict, with_tests, n_jobs):
    
    # Create target dir (or reuse existing) and write build config
    mkdir(build_dir)
    
    # Remove existing libraries from the build dir, to avoid packing unnecessary DLLs when a single-lib build is done after a separate-libs build. This also ensures we really built a new DLL in the end.
    # Leave the object files in place to reuse as much as possible, though.
    for lib in build_dir.glob(Host.libname_glob):
        lib.unlink()
    
    # Write GN config
    config_str = serialize_gn_config(config_dict)
    (build_dir/"args.gn").write_text(config_str)
    
    ninja_args = []
    if n_jobs is not None:
        ninja_args.extend(["-j", str(n_jobs)])
    
    targets = ["pdfium"]
    if with_tests:
        targets.append("pdfium_unittests")
    
    build_dir_rel = build_dir.relative_to(PDFIUM_DIR)
    run_cmd(["gn", "gen", str(build_dir_rel)], cwd=PDFIUM_DIR)
    run_cmd(["ninja", *ninja_args, "-C", str(build_dir_rel), *targets], cwd=PDFIUM_DIR)


def test(build_dir):
    # FlateModule.Encode may fail with older zlib (generates different results)
    os.environ["GTEST_FILTER"] = "*-FlateModule.Encode"
    run_cmd([build_dir/"pdfium_unittests"], cwd=PDFIUM_DIR, check=False)


def main(build_ver=None, with_tests=False, n_jobs=None, compiler=None, clang_path=None, no_libclang_rt=False, reset=False, vendor_deps=None, compat=False):
    
    if build_ver is None:
        build_ver = SBUILD_NATIVE_PIN
    if vendor_deps is None:
        vendor_deps = set()
    if compiler is None:
        if shutil.which("gcc"):
            compiler = Compiler.gcc
        elif shutil.which("clang"):
            log("gcc not available, will try clang. Note, you may need to set up some symlinks to match the clang directory layout expected by pdfium. Also, make sure libclang_rt builtins are installed, or pass --no-libclang-rt.")
            compiler = Compiler.clang
        else:
            raise RuntimeError("Neither gcc nor clang installed.")
    if compiler is Compiler.clang:
        if clang_path is None:
            clang_path = Host.usr
        clang_ver = _get_clang_ver(clang_path)
    else:
        clang_ver = None
    
    build_dir = PDFIUM_DIR/"out"/"Default"
    config = DefaultConfig.copy()
    log(vendor_deps)
    deps_info = handle_deps(config, vendor_deps, with_tests)
    
    mkdir(SOURCES_DIR)
    full_ver = get_sources(deps_info, build_ver, with_tests, compiler, clang_ver, clang_path, no_libclang_rt, reset, vendor_deps, compat)
    setup_compiler(config, compiler, clang_ver, clang_path)
    build(build_dir, config, with_tests, n_jobs)
    if with_tests:
        test(build_dir)
    
    return pack_sourcebuild(PDFIUM_DIR, build_dir, "native", full_ver, build_ver)


def parse_args(argv):
    
    parser = argparse.ArgumentParser(
        description = "Build PDFium from source natively with system tools/libraries. This does not use Google's binary toolchain, so it should be portable across different Linux architectures. Whether this might also work on other OSes depends on PDFium's build system and the availability of a Linux-like system library environment.",
    )
    if ExtendAction is not None:  # from base.py
        parser.register("action", "extend", ExtendAction)
    
    parser.add_argument(
        "--version",
        dest = "build_ver",
        help = f"The pdfium version to use. Currently defaults to {SBUILD_NATIVE_PIN}. Pass 'main' to try the latest state.",
    )
    parser.add_argument(
        "--test",
        dest = "with_tests",
        action = "store_true",
        help = "Whether to build and run tests. Recommended, except on very slow hosts.",
    )
    parser.add_argument(
        "-j", "--jobs",
        dest = "n_jobs",
        type = int,
        metavar = "N",
        help = "The number of build jobs to use. If not given, ninja will choose this value. Pass -j $(nproc) if you wanna make sure this matches the number of processor cores.",
    )
    parser.add_argument(
        "-c", "--compiler",
        type = str.lower,
        help = "The compiler to use (gcc or clang). Defaults to gcc if available.",
    )
    parser.add_argument(
        "--reset",
        action = "store_true",
        help = "Reset those git repos that we patch, and re-apply the patches. This is necessary when making a rebuild with different patch configuration (e.g. when switching between gcc <-> clang), but is not enabled by default to avoid unintentional loss of manual changes.",
    )
    # Hint: If you have a simultaneous toolchained checkout, you could use e.g. './sbuild/toolchained/pdfium/third_party/llvm-build/Release+Asserts'
    parser.add_argument(
        "--clang-path",
        type = lambda p: Path(p).expanduser().resolve(),
        help = "Path to clang release folder, if `--compiler clang` is used. By default, we try '/usr' or similar, but your system's folder structure might not match the layout expected by pdfium. Consider creating symlinks as described in pypdfium2's README.md.",
    )
    parser.add_argument(
        "--no-libclang-rt",
        action = "store_true",
        help = "If using clang, whether to patch pdfium so that it does not insist on libclang_rt.builtins.a, and will use the compiler's default instead (commonly libgcc).",
    )
    # - libicudata pulled in from the system via `auditwheel repair` is quite big. Using vendored ICU reduces wheel size by about 10 MB (compressed).
    # - With clang, using the vendored libc++ may be desirable. Also, there is some uncertainty whether using system libc++ might be ABI-unsafe. Actually, options to use system libc++ appear to be deprecated upstream.
    parser.add_argument(
        "--vendor",
        dest = "vendor_deps",
        nargs = "+",
        action = "extend",
        help = f"Dependencies to vendor. Possible values: {VendorableDeps}. Use 'all' to vendor all of these libraries."
    )
    parser.add_argument(
        "--no-vendor",
        nargs = "+",
        action = "extend",
        help = "Dependencies not to vendor. Overrides --vendor.",
    )
    parser.add_argument(
        "--compat",
        action = "store_true",
        help = "Whether to apply a compatibility patch for older system libraries (openjpeg/freetype).",
    )
    
    args = parser.parse_args(argv)
    
    if args.compiler:
        args.compiler = Compiler[args.compiler]
    
    if args.vendor_deps:
        if args.vendor_deps == ["all"]:
            args.vendor_deps = VendorableDeps
        args.vendor_deps = set(args.vendor_deps)
        if args.no_vendor:
            args.vendor_deps -= set(args.no_vendor)
    del args.no_vendor
    
    return args


def main_cli():
    args = parse_args(sys.argv[1:])
    main(**vars(args))


if __name__ == "__main__":
    main_cli()
