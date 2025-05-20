#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause
# Related work: https://github.com/tiran/libpdfium/ and https://aur.archlinux.org/packages/libpdfium-nojs

# Known issue: This script does not currently handle rebuilds

import re
import os
import sys
import shutil
import argparse
from enum import Enum
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from pypdfium2_setup.base import *

# The pdfium version this has last been tested with. Ideally, this should be close to the release version in autorelease/record.json
# To bump this version, first test locally and update any patches as needed. Then, make a branch and run "Test Sourcebuild" on CI to see if all targets continue to work. Commit the new version to the main branch only when all is green. Better stay on an older version for a while than break a target.
# Updating and testing the patch sets can be a lot of work, so we might not want to do this too frequrently.
DEFAULT_VER = 7191
# assert DEFAULT_VER >= PDFIUM_MIN_REQ

PDFIUM_URL = "https://pdfium.googlesource.com/pdfium"
_CR_PREFIX = "https://chromium.googlesource.com/"
DEPS_URLS = dict(
    build      = _CR_PREFIX + "chromium/src/build",
    abseil     = _CR_PREFIX + "chromium/src/third_party/abseil-cpp",
    fast_float = _CR_PREFIX + "external/github.com/fastfloat/fast_float",
    gtest      = _CR_PREFIX + "external/github.com/google/googletest",
    test_fonts = _CR_PREFIX + "chromium/src/third_party/test_fonts"
)
SOURCES_DIR = ProjectDir / "sbuild" / "native"
PDFIUM_DIR = SOURCES_DIR / "pdfium"
PDFIUM_3RDPARTY = PDFIUM_DIR / "third_party"

DefaultConfig = {
    "is_debug": False,
    "use_glib": False,
    "use_remoteexec": False,
    "treat_warnings_as_errors": False,
    "clang_use_chrome_plugins": False,
    "is_component_build": True,
    "pdf_is_standalone": True,
    "pdf_enable_v8": False,
    "pdf_enable_xfa": False,
    "pdf_use_skia": False,
    "pdf_use_partition_alloc": False,
    "use_sysroot": False,
    "use_system_freetype": True,
    "pdf_bundle_freetype": False,
    "use_system_lcms2": True,
    "use_system_libjpeg": True,
    "use_system_libopenjpeg2": True,
    "use_system_libpng": True,
    "use_system_libtiff": True,
    "use_system_zlib": True,
    "use_custom_libcxx": False,
    "use_libcxx_modules": False,
}
if sys.platform.startswith("darwin"):
    DefaultConfig["mac_deployment_target"] = "10.13.0"
    DefaultConfig["use_system_xcode"] = True

Compiler = Enum("Compiler", "gcc clang")


def _get_repo(url, target_dir, rev, depth=1):
    if target_dir.exists():
        return False
    # see https://stackoverflow.com/questions/31278902/how-to-shallow-clone-a-specific-commit-with-depth-1
    # TODO: on git >= 2.49, we can use `git clone --revision ...`
    mkdir(target_dir)
    run_cmd(["git", "init"], cwd=target_dir)
    run_cmd(["git", "remote", "add", "origin", url], cwd=target_dir)
    run_cmd(["git", "fetch", "--depth", str(depth), "origin", rev], cwd=target_dir)
    run_cmd(["git", "checkout", rev], cwd=target_dir)
    return True


DEPS_RE = r"\s*'{key}': '(\w+)'"
DEPS_FIELDS = "build abseil fast_float gtest test_fonts".split(" ")

class _DeferredClass:
    
    @cached_property  # included from base.py
    def deps(self):
        # TODO get a proper parser for the DEPS file format?
        deps_content = (PDFIUM_DIR/"DEPS").read_text()
        result = {}
        for field in DEPS_FIELDS:
            field_re = DEPS_RE.format(key=f"{field}_revision")
            match = re.search(field_re, deps_content)
            assert match, f"Could not find {field!r} in DEPS file"
            result[field] = match.group(1)
        log(f"Found DEPS revisions:\n{result}")
        return result

_Deferred = _DeferredClass()


def _fetch_dep(name, target_dir):
    if target_dir.exists():
        log(f"Using existing {target_dir}")
        return False
    # parse out DEPS revisions only if we actually need them
    return _get_repo(DEPS_URLS[name], target_dir, rev=_Deferred.deps[name])


def autopatch(file, pattern, repl, is_regex, exp_count=None):
    log(f"Patch {pattern!r} -> {repl!r} (is_regex={is_regex}) on {file}")
    content = file.read_text()
    if is_regex:
        content, n_subs = re.subn(pattern, repl, content)
    else:
        n_subs = content.count(pattern)
        content = content.replace(pattern, repl)
    if exp_count is not None:
        assert n_subs == exp_count
    file.write_text(content)

def autopatch_dir(dir, globexpr, pattern, repl, is_regex, exp_count=None):
    for file in dir.glob(globexpr):
        autopatch(file, pattern, repl, is_regex, exp_count)


def get_sources(short_ver, with_tests, compiler, clang_path):
    
    full_ver, pdfium_rev, chromium_rev = handle_sbuild_vers(short_ver)
    
    is_new = _get_repo(PDFIUM_URL, PDFIUM_DIR, rev=pdfium_rev)
    if is_new:
        autopatch_dir(
            PDFIUM_DIR/"public"/"cpp", "*.h",
            r'"public/(.+)"', r'"../\1"',
            is_regex=True, exp_count=None,
        )
        # don't build the test fonts (needed for embedder tests only)
        autopatch(
            PDFIUM_DIR/"testing"/"BUILD.gn",
            r'(\s*)("//third_party/test_fonts")', r"\1# \2",
            is_regex=True, exp_count=1,
        )
    
    is_new = _fetch_dep("build", PDFIUM_DIR/"build")
    if is_new:
        # Work around error about path_exists() being undefined
        git_apply_patch(PatchDir/"siso.patch", cwd=PDFIUM_DIR/"build")
        if compiler is Compiler.gcc:
            # https://crbug.com/402282789
            git_apply_patch(PatchDir/"ffp_contract.patch", cwd=PDFIUM_DIR/"build")
        elif compiler is Compiler.clang:
            # https://crbug.com/410883044
            clang_patches = ("system_libcxx_with_clang", "avoid_new_clang_flags")
            for patchname in clang_patches:
                git_apply_patch(PatchDir/f"{patchname}.patch", cwd=PDFIUM_DIR/"build")
            # TODO should we handle other OSes here?
            # see also https://groups.google.com/g/llvm-dev/c/k3q_ATl-K_0/m/MjEb6gsCCAAJ
            lld_path = clang_path/"bin"/"ld.lld"
            autopatch(
                PDFIUM_DIR/"build"/"config"/"compiler"/"BUILD.gn",
                'ldflags += [ "-fuse-ld=lld" ]',
                f'ldflags += [ "-fuse-ld={lld_path}" ]',
                is_regex=False, exp_count=1,
            )
    
    get_shimheaders_tool(PDFIUM_DIR, rev=chromium_rev)
    
    _fetch_dep("abseil", PDFIUM_3RDPARTY/"abseil-cpp")
    _fetch_dep("fast_float", PDFIUM_3RDPARTY/"fast_float"/"src")
    if with_tests:
        _fetch_dep("gtest", PDFIUM_3RDPARTY/"googletest"/"src")
        _fetch_dep("test_fonts", PDFIUM_3RDPARTY/"test_fonts")
    
    return full_ver


def prepare(config_dict, build_dir):
    # Create an empty gclient config
    (PDFIUM_DIR/"build"/"config"/"gclient_args.gni").touch(exist_ok=True)
    # Unbundle ICU
    # alternatively, we could call build/linux/unbundle/replace_gn_files.py --system-libraries icu
    (PDFIUM_3RDPARTY/"icu").mkdir(exist_ok=True)
    shutil.copyfile(
        PDFIUM_DIR/"build"/"linux"/"unbundle"/"icu.gn",
        PDFIUM_3RDPARTY/"icu"/"BUILD.gn"
    )
    # Create target dir and write build config
    mkdir(build_dir)
    config_str = serialize_gn_config(config_dict)
    (build_dir/"args.gn").write_text(config_str)


def build(with_tests, build_dir, n_jobs):
    
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


def _get_clang_ver(clang_path):
    from packaging.version import Version
    try_libpaths = [
        clang_path/"lib"/"clang",
        clang_path/"lib64"/"clang",
    ]
    libpath = next(filter(Path.exists, try_libpaths))
    candidates = (Version(p.name) for p in libpath.iterdir() if re.fullmatch(r"[\d\.]+", p.name))
    version = max(candidates)
    return version.major


def setup_compiler(config, compiler, clang_path):
    if compiler is Compiler.gcc:
        config["is_clang"] = False
    elif compiler is Compiler.clang:
        assert clang_path, "Clang path must be set"
        clang_version = _get_clang_ver(clang_path)
        config.update({
            "is_clang": True,
            "clang_base_path": str(clang_path),
            "clang_version": clang_version,
        })
    else:
        assert False, f"Unhandled compiler {compiler}"


def main_api(build_ver=None, with_tests=False, n_jobs=None, compiler=None, clang_path=None):
    
    if build_ver is None:
        build_ver = DEFAULT_VER
    if compiler is None:
        if shutil.which("gcc"):
            compiler = Compiler.gcc
        elif shutil.which("clang"):
            log("gcc not available, will try clang. Note, you may need to set up some symlinks to match the clang directory layout expected by pdfium. Also, make sure libclang_rt builtins are installed.")
            compiler = Compiler.clang
        else:
            raise RuntimeError("Neither gcc nor clang installed.")
    if compiler is Compiler.clang and clang_path is None:
        clang_path = Host.usr
    
    mkdir(SOURCES_DIR)
    full_ver = get_sources(build_ver, with_tests, compiler, clang_path)
    
    build_dir = PDFIUM_DIR/"out"/"Default"
    config = DefaultConfig.copy()
    setup_compiler(config, compiler, clang_path)
    
    prepare(config, build_dir)
    build(with_tests, build_dir, n_jobs)
    
    if with_tests:
        test(build_dir)
    
    post_ver = handle_sbuild_postver(build_ver, PDFIUM_DIR)
    pack_sourcebuild(PDFIUM_DIR, build_dir, full_ver, **post_ver)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description = "Build PDFium from source natively with system tools/libraries. This does not use Google's binary toolchain, so it should be portable across different Linux architectures. Whether this might also work on other OSes depends on PDFium's build system and the availability of a Linux-like system library environment.",
    )
    parser.add_argument(
        "--version",
        dest = "build_ver",
        help = f"The pdfium version to use. Currently defaults to {DEFAULT_VER}. Pass 'main' to try the latest state.",
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
        help = "The number of build jobs to use. If not given, ninja will choose this value. Pass -j $(nprocs) if you wanna make sure this matches the number of processor cores.",
    )
    parser.add_argument(
        "-c", "--compiler",
        type = str.lower,
        help = "The compiler to use (gcc or clang). By default, gcc is preferred.",
    )
    # Hint: If you have a simultaneous toolchained checkout, you could use e.g. './sbuild/toolchained/pdfium/third_party/llvm-build/Release+Asserts'
    parser.add_argument(
        "--clang-path",
        type = lambda p: Path(p).expanduser().resolve(),
        help = "Path to clang release folder, without trailing slash. Passing `--compiler clang` is a pre-requisite. By default, we try '/usr' or similar, but your system's folder structure might not match the layout expected by pdfium. Consider creating symlinks as described in pypdfium2's README.md.",
    )
    args = parser.parse_args(argv)
    if args.compiler:
        args.compiler = Compiler[args.compiler]
    return args


def main_cli():
    args = parse_args(sys.argv[1:])
    main_api(**vars(args))


if __name__ == "__main__":
    main_cli()
