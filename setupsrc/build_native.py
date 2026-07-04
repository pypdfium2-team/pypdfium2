#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause
# Related work: https://github.com/tiran/libpdfium and https://aur.archlinux.org/packages/libpdfium-nojs

import os
import re
import sys
import shutil
import argparse
from enum import Enum
from pathlib import Path
import urllib.request as url_request

# local
from base import *
from _build_helpers import *

_CR_PREFIX = "https://chromium.googlesource.com/"
DEPS_URLS = dict(
    pdfium     = "https://pdfium.googlesource.com/pdfium",
    build      = _CR_PREFIX + "chromium/src/build",
    abseil     = _CR_PREFIX + "chromium/src/third_party/abseil-cpp",
    fast_float = _CR_PREFIX + "external/github.com/fastfloat/fast_float",
    simdutf    = _CR_PREFIX + "chromium/src/third_party/simdutf",
    catapult   = _CR_PREFIX + "catapult",  # android
    # vendorable dependencies
    icu         = _CR_PREFIX + "chromium/deps/icu",
    buildtools  = _CR_PREFIX + "chromium/src/buildtools",
    libcxx      = _CR_PREFIX + "external/github.com/llvm/llvm-project/libcxx",
    libcxxabi   = _CR_PREFIX + "external/github.com/llvm/llvm-project/libcxxabi",
    llvm_libc   = _CR_PREFIX + "external/github.com/llvm/llvm-project/libc",
    freetype    = _CR_PREFIX + "chromium/src/third_party/freetype2",
    jpeg_turbo  = _CR_PREFIX + "chromium/deps/libjpeg_turbo",
    nasm_source = _CR_PREFIX + "chromium/deps/nasm",
    libpng      = _CR_PREFIX + "chromium/src/third_party/libpng",
    zlib        = _CR_PREFIX + "chromium/src/third_party/zlib",
    harfbuzz    = _CR_PREFIX + "external/github.com/harfbuzz/harfbuzz",
    # unittests
    gtest      = _CR_PREFIX + "external/github.com/google/googletest",
    test_fonts = _CR_PREFIX + "chromium/src/third_party/test_fonts",
)
SOURCES_DIR = ProjectDir / "sbuild" / "native"
PDFIUM_DIR = SOURCES_DIR / "pdfium"
PDFIUM_DIR_build = PDFIUM_DIR / "build"
PDFIUM_3RDPARTY = PDFIUM_DIR / "third_party"
CUSTOM_TOOLCHAIN_DIR = PDFIUM_DIR_build/"toolchain"/"linux"/"custom"
# for docs / available options, see the comments in //build/toolchain/gcc_toolchain.gni - they're really helpful
# further options e.g. enable_linker_map, extra_asmflags, shlib_extension
# see also https://chromium.googlesource.com/chromium/src/+/6488187212e7e2f1c1decb5dcf72d4fce888428a/build/toolchain/linux/unbundle/
CUSTOM_TOOLCHAIN_TEMPL = """\
import("//build/toolchain/gcc_toolchain.gni")

gcc_toolchain("default") {
  cc = "%(CC)s"
  cxx = "%(CXX)s"
  ld = cxx
  
  _toolprefix = "%(TOOLPREFIX)s"
  ar = _toolprefix + "ar"
  nm = _toolprefix + "nm"
  readelf = _toolprefix + "readelf"
  
  extra_cflags = getenv("CFLAGS")
  extra_cppflags = getenv("CPPFLAGS")
  extra_cxxflags = getenv("CXXFLAGS")
  extra_ldflags = getenv("LDFLAGS")
  
  toolchain_args = {
    current_cpu = current_cpu
    current_os = current_os
  }
}
"""

Compiler = Enum("Compiler", "gcc clang")

DefaultConfig = {
    "is_debug": False,
    "use_glib": False,
    "use_siso": False,
    "treat_warnings_as_errors": False,
    "clang_use_chrome_plugins": False,
    "is_component_build": False,
    "pdf_is_standalone": True,
    "pdf_enable_v8": False,
    "pdf_enable_xfa": False,
    "pdf_use_skia": False,
    "pdf_use_partition_alloc": False,
    "use_sysroot": False,
    "use_cxx23": False,
}

IS_ANDROID = Host.system == SysNames.android
if IS_ANDROID:
    DefaultConfig.update({
        "sysroot": str(Host.usr.parent),
        "current_os": "android",
        "target_os": "android",
        "use_mold": False,
    })
    DefaultConfig["use_sysroot"] = True
    # On Android, it seems that the build system's CPU type statically defaults to "arm", but we want this script to be host-adaptive (plus, "arm64" is the more likely candidate).
    # TODO(future) refactor platform constants from base.py so we can access abstracted OS/CPU separately through sub-attributes
    AndroidCPUMap = {"aarch64": "arm64", "armv7l": "arm", "x86_64": "x64", "i686": "x86"}
    raw_cpu = Host._raw_machine
    if raw_cpu in AndroidCPUMap:
        cpu = AndroidCPUMap[raw_cpu]
        DefaultConfig.update(current_cpu=cpu, target_cpu=cpu)
    else:
        log(f"Warning: Unknown Android CPU {raw_cpu}")


class DepsFetcher:
    
    def __init__(self, deps_info):
        self.deps_info = deps_info

    def fetch(self, name, target_dir, reset=False):
        if target_dir.exists():
            if reset:
                log(f"{target_dir.name}: Discarding unstaged changes as per --reset option.")
                run_cmd(["git", "restore", "."], cwd=target_dir)
                return True
            else:
                return False
        mkdir(target_dir.parent)  # v assuming git >= 2.49.0
        run_cmd(["git", "clone", "--depth=1", "--revision", self.deps_info[name], DEPS_URLS[name], target_dir.name], cwd=target_dir.parent)
        return True


DEPS_RE = r"\s*'{key}': '(\w+)'"

class _DeferredDeps:
    
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
    
    def __getitem__(self, key):
        out = self.deps[key]
        self.__getitem__ = self.deps.__getitem__  # optimize
        return out


def handle_deps(config, vendor_deps, with_tests):
    
    deps_fields = ["build", "abseil", "fast_float", "simdutf"]
    if IS_ANDROID:
        deps_fields.append("catapult")
    
    if "libc++" in vendor_deps:
        deps_fields += ("buildtools", "libcxx", "libcxxabi", "llvm_libc")
    else:
        config["use_custom_libcxx"] = False
    
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
    
    if "harfbuzz" in vendor_deps:
        deps_fields.append("harfbuzz")
    else:
        config["use_system_harfbuzz"] = True
    
    if "lcms2" not in vendor_deps:
        config["use_system_lcms2"] = True
    if "openjpeg" not in vendor_deps:
        config["use_system_libopenjpeg2"] = True
    if "libtiff" not in vendor_deps:
        config["use_system_libtiff"] = True
    
    if with_tests:
        deps_fields += ("gtest", "test_fonts")
    
    return _DeferredDeps(deps_fields)

VendorableDeps = ("libc++", "icu", "freetype", "libjpeg", "libpng", "zlib", "lcms2", "openjpeg", "libtiff", "harfbuzz")


_SHIMHEADERS_URL = "https://raw.githubusercontent.com/chromium/chromium/{rev}/tools/generate_shim_headers/generate_shim_headers.py"

def _get_shimheaders_tool(pdfium_dir, rev="main"):

    tools_dir = pdfium_dir / "tools" / "generate_shim_headers"
    shimheaders_file = tools_dir / "generate_shim_headers.py"
    shimheaders_url = _SHIMHEADERS_URL.format(rev=rev)

    if not shimheaders_file.exists():
        log(f"Downloading {shimheaders_file.name} at revision {rev}")
        mkdir(tools_dir)
        url_request.urlretrieve(shimheaders_url, shimheaders_file)


def get_sources(deps_info, short_ver, with_tests, compiler, clang_ver, clang_path, no_libclang_rt, reset, vendor_deps):
    
    assert not IGNORE_FULLVER
    full_ver, pdfium_rev, chromium_rev = handle_sbuild_vers(short_ver)
    
    # pass through reset only for the repositories we actually patch
    df = DepsFetcher({"pdfium": pdfium_rev})
    do_patches = df.fetch("pdfium", PDFIUM_DIR, reset=reset)
    if do_patches:
        shared_autopatches(PDFIUM_DIR)
        autopatch(
            PDFIUM_DIR/"testing"/"BUILD.gn",
            r'(\s*)("//third_party/test_fonts")', r"\1# \2",
            is_regex=True, exp_count=1,
        )
        if sys.byteorder == "big":
            git_apply_patch(PatchDir/"bigendian.patch", cwd=PDFIUM_DIR)
    
    df = DepsFetcher(deps_info)
    do_patches = df.fetch("build", PDFIUM_DIR_build, reset=reset)
    if compiler is Compiler.gcc:  # regardless of do_patches
        # declare custom GCC toolchain
        mkdir(CUSTOM_TOOLCHAIN_DIR)
        (CUSTOM_TOOLCHAIN_DIR/"BUILD.gn").write_text(
            CUSTOM_TOOLCHAIN_TEMPL % query_envs(CC="gcc", CXX="g++", TOOLPREFIX="")
        )
        # https://crbug.com/402282789
        # gcc_toolchain.gni says on extra_cppflags:
        # > Extra flags to be appended when compiling both C and C++ files. "CPP" stands for "C PreProcessor" in this context, although it can be used for non-preprocessor flags as well. Not to be confused with "CXX" (which follows).
        env_append("CPPFLAGS", "-ffp-contract=off", " ")
    if do_patches:
        # it says gcc_toolchain but actually needed for clang as well
        # -> upstream fix merged, can be removed or put behind version guard once pdfium rolls //build and we update pdfium
        git_apply_patch(PatchDir/"gcc_toolchain.patch", cwd=PDFIUM_DIR_build)
        if IS_ANDROID:  # fix linkage step
            git_apply_patch(PatchDir/"android_native.patch", cwd=PDFIUM_DIR_build)
        if compiler is Compiler.clang:
            if clang_ver < 23:
                git_apply_patch(PatchDir/"clang_22_compat.patch", cwd=PDFIUM_DIR_build)
            if no_libclang_rt:
                git_apply_patch(PatchDir/"no_libclang_rt.patch", cwd=PDFIUM_DIR_build)
            if "libc++" not in vendor_deps:
                # historically, https://crbug.com/410883044
                autopatch(
                    PDFIUM_DIR_build/"config"/"BUILDCONFIG.gn",
                    "use_libcxx_modules = is_clang",
                    "use_libcxx_modules = false",
                    is_regex=False, exp_count=2,
                )
            # TODO should we handle other OSes here?
            # see also https://groups.google.com/g/llvm-dev/c/k3q_ATl-K_0/m/MjEb6gsCCAAJ
            lld_path = clang_path/"bin"/"ld.lld"
            autopatch(
                PDFIUM_DIR_build/"config"/"compiler"/"BUILD.gn",
                'ldflags += [ "-fuse-ld=lld" ]',
                f'ldflags += [ "-fuse-ld={lld_path}" ]',
                is_regex=False, exp_count=1,
            )
            if Host._libc_name == "musl":
                n_subs = 0
                for pattern in ("-unknown-linux-gnu", "-linux-gnu"):  # two-pass
                    n_subs += autopatch(
                        PDFIUM_DIR_build/"config"/"compiler_cpu_abi.gn",
                        pattern, "-alpine-linux-musl",
                        is_regex=False,
                    )
                # confirm there have been a couple of substitutions
                assert n_subs > 3  # likely much more than that
        # Create pseudo gclient config included by //build
        (PDFIUM_DIR_build/"config"/"gclient_args.gni").write_text("build_with_chromium = false")
    
    df.fetch("abseil", PDFIUM_3RDPARTY/"abseil-cpp")
    df.fetch("fast_float", PDFIUM_3RDPARTY/"fast_float"/"src")
    df.fetch("simdutf", PDFIUM_3RDPARTY/"simdutf")
    if IS_ANDROID:
        df.fetch("catapult", PDFIUM_3RDPARTY/"catapult")
    
    if "libc++" in vendor_deps:
        df.fetch("buildtools", PDFIUM_DIR/"buildtools")
        df.fetch("libcxx", PDFIUM_3RDPARTY/"libc++"/"src")
        df.fetch("libcxxabi", PDFIUM_3RDPARTY/"libc++abi"/"src")
        df.fetch("llvm_libc", PDFIUM_3RDPARTY/"llvm-libc"/"src")
    
    if "icu" in vendor_deps:
        df.fetch("icu", PDFIUM_3RDPARTY/"icu")
    else:
        # unbundle (alternatively, we could call build/linux/unbundle/replace_gn_files.py --system-libraries icu)
        (PDFIUM_3RDPARTY/"icu").mkdir(exist_ok=True)
        shutil.copyfile(PDFIUM_DIR_build/"linux"/"unbundle"/"icu.gn", PDFIUM_3RDPARTY/"icu"/"BUILD.gn")
    
    if "freetype" in vendor_deps:
        df.fetch("freetype", PDFIUM_3RDPARTY/"freetype"/"src")
    if "libjpeg" in vendor_deps:
        df.fetch("jpeg_turbo", PDFIUM_3RDPARTY/"libjpeg_turbo")
        df.fetch("nasm_source", PDFIUM_3RDPARTY/"nasm")
    if "libpng" in vendor_deps:
        df.fetch("libpng", PDFIUM_3RDPARTY/"libpng")
    if "zlib" in vendor_deps:
        df.fetch("zlib", PDFIUM_3RDPARTY/"zlib")
    if "harfbuzz" in vendor_deps:
        df.fetch("harfbuzz", PDFIUM_3RDPARTY/"harfbuzz"/"src")
    
    if with_tests:
        df.fetch("gtest", PDFIUM_3RDPARTY/"googletest"/"src")
        df.fetch("test_fonts", PDFIUM_3RDPARTY/"test_fonts")
    
    _get_shimheaders_tool(PDFIUM_DIR, rev=chromium_rev)
    
    return full_ver


def setup_compiler(config, compiler, clang_ver, clang_path):
    if compiler is Compiler.gcc:
        config["is_clang"] = False
        # this ought to match CUSTOM_TOOLCHAIN_DIR
        config["custom_toolchain"] = "//build/toolchain/linux/custom:default"
        config["host_toolchain"] = "//build/toolchain/linux/custom:default"
    elif compiler is Compiler.clang:
        assert clang_path, "Clang path must be set"
        config.update({
            "is_clang": True,
            "clang_base_path": str(clang_path),  # without trailing slash
            "clang_version": clang_ver,
        })
    else:
        assert False, f"Unhandled compiler {compiler}"


_SysrootMap = sysroot_cpu = {
    "x86_64":   ("amd64",    "bullseye"),
    "i686":     ("i386",     "bullseye"),
    "armv7l":   ("armhf",    "bullseye"),
    "armv8l":   ("armhf",    "bullseye"),
    "aarch64":  ("arm64",    "bullseye"),
    "ppc64le":  ("ppc64el",  "bullseye"),
    "mipsle":   ("mipsel",   "bullseye"),
    "mips64le": ("mips64el", "bullseye"),
    "riscv64":  ("riscv64",  "trixie"),
}

def handle_sysroot(use_sysroot, config, compiler, vendor_deps):
    
    if not (use_sysroot and sys.platform.startswith("linux") and Host._libc_name == "glibc"):
        return
    
    sysroot_cpu, deb_name = _SysrootMap.get(Host._raw_machine, (Host._raw_machine, "bullseye"))
    sysroot_script = PDFIUM_DIR/"build"/"linux"/"sysroot_scripts"/"install-sysroot.py"
    run_cmd([sys.executable, str(sysroot_script), "--arch", sysroot_cpu], cwd=PDFIUM_DIR)
    
    config["use_sysroot"] = True
    config["sysroot"] = f"//build/linux/debian_{deb_name}_{sysroot_cpu}-sysroot"
    
    if compiler is Compiler.gcc or "libc++" not in vendor_deps:
        log("Warning: --use-sysroot works best with clang and vendored libc++. It may or may not work with GCC / system libc++.")


def build(build_dir, config_dict, with_tests, n_jobs):
    
    # Create target dir, or reuse existing
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


def test(build_dir, vendor_deps, compiler):
    gtest_filter = []
    # obscure failure if either system libc++ or gcc config (or both) are used
    if "libc++" not in vendor_deps or compiler is Compiler.gcc:
        gtest_filter.append("RetainPtr.SetContains")
    # may fail with older zlib (generates different results)
    if "zlib" not in vendor_deps:
        gtest_filter.append("FlateModule.Encode")
    if Host._libc_name == "musl":
        gtest_filter.append("WideString.FormatString")  # FIXME?
    if Host._raw_machine == "s390x":
        gtest_filter.append("CPDFPageImageCacheTest.RenderBug1924")  # FIXME actually crashes
    if gtest_filter:
        os.environ["GTEST_FILTER"] = "*:-" + ":".join(gtest_filter)
    run_cmd([build_dir/"pdfium_unittests"], cwd=PDFIUM_DIR)


def main(build_ver=None, with_tests=False, n_jobs=None, compiler=None, clang_path=None, no_libclang_rt=False, clang_as_gcc=False, reset=False, vendor_deps=None, use_sysroot=False):
    
    if build_ver is None:
        build_ver = SBUILD_NATIVE_PIN
    elif build_ver == "latest":
        build_ver = PdfiumVer.get_latest_upstream().build
    elif build_ver == "latest-binaries":
        build_ver = PdfiumVer.get_latest()
    
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
    
    clang_ver = None
    if compiler is Compiler.clang:
        if clang_path is None:
            clang_path = Host.usr
        clang_ver = get_clang_version(clang_path)
        if clang_ver < 22:
            log("Warning: Clang below version 22 is not supported with upstream's clang config - implicitly switching to --clang-as-gcc mode. If you mean to manually patch pdfium's //build for compatibility with older clang (possible, but no fun to maintain), take out this check.")
            clang_as_gcc = True
            clang_ver = None
        if clang_as_gcc:
            env_prepend("PATH", str(clang_path/"bin"), os.pathsep)
            set_envs(CC="clang", CXX="clang++", TOOLPREFIX="llvm-")
            compiler = Compiler.gcc
    
    build_dir = PDFIUM_DIR/"out"/"Default"
    config = DefaultConfig.copy()
    log(vendor_deps)
    deps_info = handle_deps(config, vendor_deps, with_tests)
    
    mkdir(SOURCES_DIR)
    full_ver = get_sources(deps_info, build_ver, with_tests, compiler, clang_ver, clang_path, no_libclang_rt, reset, vendor_deps)
    setup_compiler(config, compiler, clang_ver, clang_path)
    handle_sysroot(use_sysroot, config, compiler, vendor_deps)
    build(build_dir, config, with_tests, n_jobs)
    if with_tests:
        test(build_dir, vendor_deps, compiler)
    
    return pack_sourcebuild(PDFIUM_DIR, build_dir, "native", full_ver, build_ver)


def parse_args(argv):
    
    parser = argparse.ArgumentParser(
        formatter_class = argparse.RawTextHelpFormatter,
        description = """\
Build PDFium from source natively with a self-managed checkout and system tools/libraries (depending on config).

This does not use Google's binary toolchain, so it should be portable across different Linux architectures.
Whether this might also work on other OSes depends on PDFium's build system and the availability of a Linux-like system library environment.
See the notes in pypdfium2's README.md for more information.

Note that pdfium is picky about the GN version, and requires newer GN than what stable distributions usually provide. Outdated GN may fail with the most obscure errors.
We suggest that you `pip install -r req/gn.txt` which will install an appropriate version of gn-dist from PyPI. gn-dist is also maintained by the pypdfium2 authors.

Likewise, clang users should note that pdfium expects a very recent version of clang.
Upstream does not aim for compatibility with clang older than the version they currently use.
pypdfium2 patches pdfium for compatibility with clang 22. For versions older than that, --clang-as-gcc mode is implicitly enabled.

In GCC build mode, the usual environment variables are respected: CC, CXX, CFLAGS, CPPFLAGS, CXXFLAGS, LDFLAGS. Also, a TOOLPREFIX can be set for ar/nm/readelf.
In clang mode, --clang-path lets you choose the clang build used, but flags are not honored yet.

Some params take a default from an environment variable, for easy passthrough with cibuildwheel.\
""",
    )
    if ExtendAction is not None:  # from base.py
        parser.register("action", "extend", ExtendAction)
    
    parser.add_argument(
        "--version",
        dest = "build_ver",
        default = (os.environ.get("PDFIUM_VER") or None),
        help = f"The pdfium version to use. Either a literal version number, or 'main', 'latest' or 'latest-binaries'. Defaults to the pinned version {SBUILD_NATIVE_PIN}, or $PDFIUM_VER if set.",
    )
    parser.add_argument(
        "--test",
        dest = "with_tests",
        action = "store_true",
        default = bool(int( os.environ.get("TEST_PDFIUM", 0) )),
        help = "Whether to build and run tests. Recommended, except on very slow hosts. Defaults to $TEST_PDFIUM.",
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
        help = "Discard unstaged changes on those git repos that we patch, and re-apply the patches. Uses `git restore` under the hood. This is necessary when making a rebuild with different patch configuration (e.g. when switching between gcc <-> clang), but is not enabled by default to avoid unintentional loss of manual changes.",
    )
    # Hint: If you have a simultaneous toolchained checkout, you could use e.g. './sbuild/toolchained/pdfium/third_party/llvm-build/Release+Asserts'
    parser.add_argument(
        "--clang-path",
        type = lambda p: Path(p).expanduser().resolve(),
        help = "Path to clang release folder, if `--compiler clang` is used. By default, we try `/usr` or similar, but your system's folder structure might not match the layout expected by pdfium. Consider creating symlinks as described in pypdfium2's README.md.",
    )
    parser.add_argument(
        "--no-libclang-rt",
        action = "store_true",
        help = "If using clang, whether to patch pdfium so that it does not insist on libclang_rt.builtins.a, and will use the compiler's default instead (commonly libgcc).",
    )
    parser.add_argument(
        "--clang-as-gcc",
        action = "store_true",
        help = "Use clang, but pretend to pdfium's build system that it were gcc. Passing `--compiler clang` is a prerequisite.",
    )
    # nb: libicudata pulled in from the system via `auditwheel repair` is quite big. Using vendored ICU reduces wheel size by about 10 MB (compressed).
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
        "--use-sysroot",
        action = "store_true",
        default = bool(int( os.environ.get("USE_SYSROOT", 0) )),
        help = "Attempt to use a Google-processed Debian sysroot for the build. This may help achieve a lower glibc requirement. This option is Linux glibc only, and ignored on other platforms. If no sysroot is available for the host CPU, this will fail.",
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
