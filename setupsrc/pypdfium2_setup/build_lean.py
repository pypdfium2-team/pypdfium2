#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause
# Related work: https://github.com/tiran/libpdfium/ and https://aur.archlinux.org/packages/libpdfium-nojs

# NOTE So far, we have only tested this script on Linux, but the general idea should work on any common OS, provided the necessary tools and libraries are available.
# In other words, this script should be portable as far as pdfium's build system and code is.
# On Windows, you might be better off with the toolchained build, though, due to lack of a Unix-like system library environment.

# Known issues:
# - This script does not currently handle rebuilds. You have to manually delete the pdfium/ directory if you want to rebuild with a different version. In the future, we might want to use git repositories rather than tarballs to make tasks like version switching or patching more straightforward.

import re
import os
import sys
import shutil
import argparse
from enum import Enum
from pathlib import Path
from urllib.request import urlretrieve

sys.path.insert(0, str(Path(__file__).parents[1]))
import pypdfium2_setup.base as pkgbase
from pypdfium2_setup.base import log, mkdir

_CR_PREFIX = "https://chromium.googlesource.com/"
PDFIUM_URL = "https://pdfium.googlesource.com/pdfium/+archive/{rev}.tar.gz#/pdfium-{name}.tar.gz"
DEPS_URLS = dict(
    build = _CR_PREFIX + "chromium/src/build.git/+archive/{rev}.tar.gz#/build-{rev}.tar.gz",
    abseil = _CR_PREFIX + "chromium/src/third_party/abseil-cpp/+archive/{rev}.tar.gz#/abseil-cpp-{rev}.tar.gz",
    fast_float = _CR_PREFIX + "external/github.com/fastfloat/fast_float.git/+archive/{rev}.tar.gz#/fast_float-{rev}.tar.gz",
    gtest = _CR_PREFIX + "external/github.com/google/googletest.git/+archive/{rev}.tar.gz#/gtest-{rev}.tar.gz",
    test_fonts = _CR_PREFIX + "chromium/src/third_party/test_fonts.git/+archive/{rev}.tar.gz#/test_fonts-{rev}.tar.gz"
)
SHIMHEADERS_URL = _CR_PREFIX + "chromium/src/+archive/{rev}/tools/generate_shim_headers.tar.gz#/generate_shim_headers-{name}.tar.gz"

SOURCES_DIR = pkgbase.ProjectDir / "sbuild" / "lean"
PDFIUM_DIR = SOURCES_DIR / "pdfium"
PDFIUM_3RDPARTY = PDFIUM_DIR / "third_party"

DefaultConfig = {
    "use_sysroot": False,
    "clang_use_chrome_plugins": False,
    "treat_warnings_as_errors": False,
    "use_remoteexec": False,
    "is_debug": False,
    "is_component_build": True,
    "pdf_is_standalone": True,
    "pdf_enable_v8": False,
    "pdf_enable_xfa": False,
    "pdf_use_skia": False,
    "pdf_use_partition_alloc": False,
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


if sys.version_info < (3, 8):
    # NOTE alternatively, we could write our own cached property backport with python's descriptor protocol
    from functools import lru_cache
    def cached_property(func):
        return property( lru_cache(maxsize=1)(func) )
else:
    from functools import cached_property


# tar unpacking template adapted from https://gist.github.com/mara004/6fe0ac15d0cf303bed0aea2f22d8531f

if sys.version_info >= (3, 11, 4):  # PEP 706
    def safer_tar_unpack(archive_path, dest_dir):
        shutil.unpack_archive(archive_path, dest_dir, format="tar", filter="data")

else:  # workaround
    import tarfile
    
    def safer_tar_unpack(archive_path, dest_dir):
        dest_dir = Path(dest_dir).resolve()
        with tarfile.open(archive_path) as tar:
            for m in tar.getmembers():
                if not ((m.isfile() or m.isdir()) and dest_dir in (dest_dir/m.name).resolve().parents):
                    raise RuntimeError("Path traversal, symlink or non-file member in tar archive (potentially malicious).")
            tar.extractall(dest_dir)


def _fetch_archive(archive_url, dest_path):
    
    if dest_path.exists():
        log(f"Using existing {dest_path}")
        return False
    
    name = archive_url.rsplit("/")[-1]
    archive_path = SOURCES_DIR/name
    if not archive_path.exists():
        log(f"Fetching {archive_url!r} to {archive_path} ...")
        urlretrieve(archive_url, archive_path)
    
    log(f"Unpacking {archive_path} to {dest_path} ...")
    safer_tar_unpack(archive_path, dest_path)
    
    return True


DEPS_RE = r"\s*'{key}': '(\w+)'"
DEPS_FIELDS = "build abseil fast_float gtest test_fonts".split(" ")

class _DeferredClass:
    
    @cached_property
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
    return _fetch_archive(DEPS_URLS[name].format(rev=_Deferred.deps[name]), target_dir)


def autopatch(file, pattern, repl, is_regex):
    log(f"Patch {pattern!r} -> {repl!r} (is_regex={is_regex}) on {file}")
    content = file.read_text()
    if is_regex:
        content, n_subs = re.subn(pattern, repl, content)
        assert n_subs > 0
    else:
        content = content.replace(pattern, repl)
    file.write_text(content)

def autopatch_dir(dir, globexpr, pattern, repl, is_regex):
    for file in dir.glob(globexpr):
        autopatch(file, pattern, repl, is_regex)

def classic_patch(patchfile, cwd):
    # alternatively, this might work: pkgbase.git_apply_patch(..., git_args=("--git-dir=/dev/null", "--work-tree=."))
    # FIXME managing patches without an actual git repository is nasty either way
    pkgbase.run_cmd(["patch", "-p1", "--ignore-whitespace", "-i", str(patchfile)], cwd=cwd)


def _format_url(url, rev):
    return url.format(rev=rev, name=rev.rsplit("/")[-1])

def get_sources(short_ver, with_tests, compiler):
    
    if short_ver == "main":
        pdfium_rev = "refs/heads/main"
        chromium_rev = pdfium_rev
        full_ver = pkgbase.PdfiumVer.get_latest_upstream()
    else:
        full_ver = pkgbase.PdfiumVer.to_full(short_ver)
        full_ver_str = ".".join(str(v) for v in full_ver)
        pdfium_rev = f"refs/heads/chromium/{short_ver}"
        chromium_rev = f"refs/tags/{full_ver_str}"
    
    is_new = _fetch_archive(_format_url(PDFIUM_URL, pdfium_rev), PDFIUM_DIR)
    if is_new:
        autopatch_dir(PDFIUM_DIR/"public"/"cpp", "*.h", r'"public/(.+)"', r'"../\1"', is_regex=True)
        # don't build the test fonts (needed for embedder tests only)
        autopatch(PDFIUM_DIR/"testing"/"BUILD.gn", r'(\s*)("//third_party/test_fonts")', r"\1# \2", is_regex=True)

    is_new = _fetch_dep("abseil", PDFIUM_3RDPARTY/"abseil-cpp")
    if is_new:
        autopatch(PDFIUM_3RDPARTY/"abseil-cpp"/"BUILD.gn", 'component("absl")', 'static_library("absl")', is_regex=False)
    
    is_new = _fetch_dep("build", PDFIUM_DIR/"build")
    if is_new:
        # Work around error about path_exists() being undefined
        classic_patch(pkgbase.PatchDir/"siso.patch", cwd=PDFIUM_DIR/"build")
        if compiler is Compiler.clang:
            clang_patches = ("system_libcxx_with_clang", "avoid_new_clang_flags")
            for patchname in clang_patches:
                classic_patch(pkgbase.PatchDir/f"{patchname}.patch", cwd=PDFIUM_DIR/"build")
            autopatch(PDFIUM_DIR/"build"/"config"/"compiler"/"BUILD.gn", 'ldflags += [ "-fuse-ld=lld" ]', 'ldflags += [ "-fuse-ld=/usr/bin/ld.lld" ]', is_regex=False)
    
    _fetch_dep("fast_float", PDFIUM_3RDPARTY/"fast_float"/"src")
    _fetch_archive(_format_url(SHIMHEADERS_URL, chromium_rev), PDFIUM_DIR/"tools"/"generate_shim_headers")
    
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
    config_str = pkgbase.serialise_gn_config(config_dict)
    (build_dir/"args.gn").write_text(config_str)


def build(with_tests, build_dir, compiler):
    
    if compiler is Compiler.gcc:
        # https://issues.chromium.org/issues/402282789
        cppflags = "-ffp-contract=off"
        orig_cppflags = os.environ.get("CPPFLAGS", "")
        if orig_cppflags:
            cppflags += " " + orig_cppflags
        os.environ["CPPFLAGS"] = cppflags
    
    targets = ["pdfium"]
    if with_tests:
        targets.append("pdfium_unittests")
    
    build_dir_rel = build_dir.relative_to(PDFIUM_DIR)
    pkgbase.run_cmd([shutil.which("gn"), "gen", str(build_dir_rel)], cwd=PDFIUM_DIR)
    pkgbase.run_cmd([shutil.which("ninja"), "-C", str(build_dir_rel), *targets], cwd=PDFIUM_DIR)


def test(build_dir):
    # FlateModule.Encode may fail with older zlib (generates different results)
    os.environ["GTEST_FILTER"] = "*-FlateModule.Encode"
    pkgbase.run_cmd([build_dir/"pdfium_unittests"], cwd=PDFIUM_DIR, check=False)


def _get_clang_ver(clang_path):
    from packaging.version import Version
    try_libpaths = [
        clang_path/"lib"/"clang",
        clang_path/"lib64"/"clang",
    ]
    libpath = next(p for p in try_libpaths if p.exists())
    candidates = (Version(p.name) for p in libpath.iterdir() if re.fullmatch(r"[\d\.]+", p.name))
    version = max(candidates)
    return version.major


def setup_compiler(config, compiler, clang_path):
    if compiler is Compiler.gcc:
        config.update({
            "is_clang": False,
            "custom_toolchain": "//build/toolchain/linux/passflags:default",
            "host_toolchain": "//build/toolchain/linux/passflags:default",
        })
        # Set up custom flavor of GCC toolchain that supports passing flags
        mkdir(PDFIUM_DIR/"build"/"toolchain"/"linux"/"passflags")
        shutil.copyfile(
            pkgbase.PatchDir/"passflags-BUILD.gn",
            PDFIUM_DIR/"build"/"toolchain"/"linux"/"passflags"/"BUILD.gn"
        )
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


DEFAULT_VER = 7122

def main_api(build_ver=None, with_tests=False, compiler=None, clang_path=None):
    
    if build_ver is None:
        build_ver = DEFAULT_VER
    if compiler is None:
        compiler = Compiler.gcc
    if clang_path is None and os.name != "nt":
        clang_path = Path("/usr")
    
    mkdir(SOURCES_DIR)
    full_ver = get_sources(build_ver, with_tests, compiler)
    
    build_dir = PDFIUM_DIR/"out"/"Default"
    config = DefaultConfig.copy()
    setup_compiler(config, compiler, clang_path)
    
    prepare(config, build_dir)
    build(with_tests, build_dir, compiler)
    
    if with_tests:
        test(build_dir)
    
    pkgbase.pack_sourcebuild(PDFIUM_DIR, build_dir, full_ver, is_short_ver=False)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description = "Build PDFium from source natively with system tools/libraries. This does not depend on Google's binary toolchain, so it should be portable across different Linux architectures.",
    )
    parser.add_argument(
        "--version",
        dest = "build_ver",
        help = f"The pdfium version to use. Defaults to the version last tested by pypdfium2 maintainers (recommended, currently {DEFAULT_VER}). Otherwise, this can be a specific build number, or 'main' to try the latest upstream state.",
    )
    parser.add_argument(
        "--test",
        dest = "with_tests",
        action = "store_true",
        help = "Whether to build and run tests. Recommended, except on very slow hosts.",
    )
    parser.add_argument(
        "--compiler",
        type = str.lower,
        help = "The compiler to use (gcc or clang). Defaults to gcc.",
    )
    parser.add_argument(
        "--clang-path",
        type = lambda p: Path(p).expanduser().resolve(),
        help = "Path to clang release folder, without trailing slash. Passing --compiler clang is a pre-requisite. By default, we try '/usr', but your system's folder structure might not match the layout expected by pdfium. Consider creating symlinks or downloading an LLVM release.",
        # Hints:
        # - On Ubuntu/Fedora, the symlink commands are (set $VERSION and $ARCH accordingly):
        #   sudo ln -s /usr/lib/clang/$VERSION/lib/linux /usr/lib/clang/$VERSION/lib/$ARCH-unknown-linux-gnu
        #   sudo ln -s /usr/lib/clang/$VERSION/lib/linux/libclang_rt.builtins-$ARCH.a /usr/lib/clang/$VERSION/lib/linux/libclang_rt.builtins.a
        # - If you have a simultaneous toolchained checkout, you could use e.g. './sbuild/toolchained/pdfium/third_party/llvm-build/Release+Asserts'
        # - Also, it seems that Google's Clang releases can be downloaded from https://storage.googleapis.com/chromium-browser-clang/ (append the object_name in question, as in pdfium's DEPS file). Alternatively, there is depot_tools/download_from_google_storage.py
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
