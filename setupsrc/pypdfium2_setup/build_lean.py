#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause
# Related work: https://github.com/tiran/libpdfium/ and https://aur.archlinux.org/packages/libpdfium-nojs

import re
import os
import sys
import shutil
import argparse
from pathlib import Path
from urllib.request import urlretrieve

sys.path.insert(0, str(Path(__file__).parents[1]))
import pypdfium2_setup.base as pkgbase
from pypdfium2_setup.base import log, mkdir

_CHROMIUM_URL = "https://chromium.googlesource.com/"
PDFIUM_URL = "https://pdfium.googlesource.com/pdfium/+archive/{rev}.tar.gz#/pdfium-{name}.tar.gz"
DEPS_URLS = dict(
    build = _CHROMIUM_URL + "chromium/src/build.git/+archive/{rev}.tar.gz#/build-{rev}.tar.gz",
    abseil = _CHROMIUM_URL + "chromium/src/third_party/abseil-cpp/+archive/{rev}.tar.gz#/abseil-cpp-{rev}.tar.gz",
    fast_float = _CHROMIUM_URL + "external/github.com/fastfloat/fast_float.git/+archive/{rev}.tar.gz#/fast_float-{rev}.tar.gz",
    gtest = _CHROMIUM_URL + "external/github.com/google/googletest.git/+archive/{rev}.tar.gz#/gtest-{rev}.tar.gz",
    test_fonts = _CHROMIUM_URL + "chromium/src/third_party/test_fonts.git/+archive/{rev}.tar.gz#/test_fonts-{rev}.tar.gz"
)
SHIMHEADERS_URL = _CHROMIUM_URL + "chromium/src/+archive/{rev}/tools/generate_shim_headers.tar.gz#/generate_shim_headers-{name}.tar.gz"

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
    "is_clang": False,
    "custom_toolchain": "//build/toolchain/linux/passflags:default",
    "host_toolchain": "//build/toolchain/linux/passflags:default",
}
if sys.platform.startswith("darwin"):
    DefaultConfig["mac_deployment_target"] = "10.13.0"
    DefaultConfig["use_system_xcode"] = True


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
        print(f"Using existing {dest_path}")
        return False
    
    name = archive_url.rsplit("/")[-1]
    archive_path = SOURCES_DIR/name
    if not archive_path.exists():
        print(f"Fetching {archive_url!r} to {archive_path} ...")
        urlretrieve(archive_url, archive_path)
    
    print(f"Unpacking {archive_path} to {dest_path} ...")
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

def get_sources(short_ver, with_tests):
    
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
    
    _fetch_dep("fast_float", PDFIUM_3RDPARTY/"fast_float"/"src")
    _fetch_archive(_format_url(SHIMHEADERS_URL, chromium_rev), PDFIUM_DIR/"tools"/"generate_shim_headers")
    
    if with_tests:
        _fetch_dep("gtest", PDFIUM_3RDPARTY/"googletest"/"src")
        _fetch_dep("test_fonts", PDFIUM_3RDPARTY/"test_fonts")


def prepare(config_dict):
    # Create an empty gclient config
    (PDFIUM_DIR/"build"/"config"/"gclient_args.gni").touch(exist_ok=True)
    # Unbundle ICU
    # alternatively, we could call build/linux/unbundle/replace_gn_files.py --system-libraries icu
    (PDFIUM_3RDPARTY/"icu").mkdir(exist_ok=True)
    shutil.copyfile(
        PDFIUM_DIR/"build"/"linux"/"unbundle"/"icu.gn",
        PDFIUM_3RDPARTY/"icu"/"BUILD.gn"
    )
    # Set up custom flavor of GCC toolchain
    mkdir(PDFIUM_DIR/"build"/"toolchain"/"linux"/"passflags")
    shutil.copyfile(
        pkgbase.PatchDir/"passflags-BUILD.gn",
        PDFIUM_DIR/"build"/"toolchain"/"linux"/"passflags"/"BUILD.gn"
    )
    # Create target dir and write build config
    mkdir(PDFIUM_DIR/"out"/"Release")
    config_str = pkgbase.serialise_gn_config(config_dict)
    (PDFIUM_DIR/"out"/"Release"/"args.gn").write_text(config_str)


def build(with_tests):
    
    # https://issues.chromium.org/issues/402282789
    cppflags = "-ffp-contract=off"
    orig_cppflags = os.environ.get("CPPFLAGS", "")
    if orig_cppflags:
        cppflags += " " + orig_cppflags
    os.environ["CPPFLAGS"] = cppflags
    
    targets = ["pdfium"]
    if with_tests:
        targets.append("pdfium_unittests")
    
    build_path_rel = Path("out", "Release")
    pkgbase.run_cmd([shutil.which("gn"), "gen", build_path_rel], cwd=PDFIUM_DIR)
    pkgbase.run_cmd([shutil.which("ninja"), "-C", build_path_rel, *targets], cwd=PDFIUM_DIR)
    
    return PDFIUM_DIR/build_path_rel


def test(build_path):
    # FlateModule.Encode may fail with older zlib (generates different results)
    os.environ["GTEST_FILTER"] = "*-FlateModule.Encode"
    pkgbase.run_cmd([build_path/"pdfium_unittests"], cwd=PDFIUM_DIR, check=False)


DEFAULT_VER = 7122

def main_api(build_ver=None, with_tests=False):
    if build_ver is None:
        build_ver = DEFAULT_VER
    mkdir(SOURCES_DIR)
    get_sources(build_ver, with_tests)
    prepare(DefaultConfig)
    build_path = build(with_tests)
    if with_tests:
        test(build_path)


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
    return parser.parse_args(argv)


def main_cli():
    args = parse_args(sys.argv[1:])
    main_api(**vars(args))


if __name__ == "__main__":
    main_cli()
