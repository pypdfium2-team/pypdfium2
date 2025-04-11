#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause
# Inspired by https://github.com/tiran/libpdfium/

import re
import os
import sys
import shutil
import argparse
from pathlib import Path
from urllib.request import urlretrieve

sys.path.insert(0, str(Path(__file__).parents[1]))
import pypdfium2_setup.base as pkgbase

_CHROMIUM_URL = "https://chromium.googlesource.com/"
PDFIUM_URL = "https://pdfium.googlesource.com/pdfium/+archive/{revpath}.tar.gz#/pdfium-{id}.tar.gz"
DEPS_URLS = dict(
    build = _CHROMIUM_URL + "chromium/src/build.git/+archive/{rev}.tar.gz#/build-{rev}.tar.gz",
    abseil = _CHROMIUM_URL + "chromium/src/third_party/abseil-cpp/+archive/{rev}.tar.gz#/abseil-cpp-{rev}.tar.gz",
    fast_float = _CHROMIUM_URL + "external/github.com/fastfloat/fast_float.git/+archive/{rev}.tar.gz#/fast_float-{rev}.tar.gz",
    gtest = _CHROMIUM_URL + "external/github.com/google/googletest.git/+archive/{rev}.tar.gz#/gtest-{rev}.tar.gz",
    test_fonts = _CHROMIUM_URL + "chromium/src/third_party/test_fonts.git/+archive/{rev}.tar.gz#/test_fonts-{rev}.tar.gz"
)
SHIMHEADERS_URL = _CHROMIUM_URL + "chromium/src/+archive/{revpath}/tools/generate_shim_headers.tar.gz#/generate_shim_headers-{id}.tar.gz"

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


def log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


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


def get_sources(full_ver):
    short_ver = full_ver.build
    full_ver_str = ".".join(str(v) for v in full_ver)
    is_new = _fetch_archive(PDFIUM_URL.format(revpath=f"refs/heads/chromium/{short_ver}", id=short_ver), PDFIUM_DIR)
    if is_new:
        autopatch_dir(PDFIUM_DIR/"public"/"cpp", "*.h", r'"public/(.+)"', r'"../\1"', is_regex=True)
        # don't build the test fonts (needed for embedder tests only)
        autopatch(PDFIUM_DIR/"testing"/"BUILD.gn", r'(\s*)("//third_party/test_fonts")', r"\1# \2", is_regex=True)
    
    is_new = _fetch_dep("abseil", PDFIUM_3RDPARTY/"abseil-cpp")
    if is_new:
        autopatch(PDFIUM_3RDPARTY/"abseil-cpp"/"BUILD.gn", 'component("absl")', 'static_library("absl")', is_regex=False)
    
    _fetch_dep("build", PDFIUM_DIR/"build")
    _fetch_dep("fast_float", PDFIUM_3RDPARTY/"fast_float"/"src")
    _fetch_dep("gtest", PDFIUM_3RDPARTY/"googletest"/"src")
    _fetch_dep("test_fonts", PDFIUM_3RDPARTY/"test_fonts")
    # e.g. "refs/tags/{full_ver_str}", "refs/heads/main", or revision
    _fetch_archive(SHIMHEADERS_URL.format(revpath=f"refs/tags/{full_ver_str}", id=full_ver_str), PDFIUM_DIR/"tools"/"generate_shim_headers")


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
    (PDFIUM_DIR/"build"/"toolchain"/"linux"/"passflags").mkdir(exist_ok=True, parents=True)
    shutil.copyfile(
        pkgbase.PatchDir/"passflags-BUILD.gn",
        PDFIUM_DIR/"build"/"toolchain"/"linux"/"passflags"/"BUILD.gn"
    )
    # Create target dir and write build config
    (PDFIUM_DIR/"out"/"Release").mkdir(exist_ok=True, parents=True)
    config_str = pkgbase.serialise_gn_config(config_dict)
    (PDFIUM_DIR/"out"/"Release"/"args.gn").write_text(config_str)


def build():
    release_path = Path("out", "Release")
    # https://issues.chromium.org/issues/402282789
    cppflags = "-ffp-contract=off"
    orig_cppflags = os.environ.get("CPPFLAGS", "")
    if orig_cppflags:
        cppflags += " " + orig_cppflags
    os.environ["CPPFLAGS"] = cppflags
    pkgbase.run_cmd(["gn", "gen", str(release_path)], cwd=PDFIUM_DIR)
    pkgbase.run_cmd(["ninja", "-C", str(release_path), "pdfium", "pdfium_unittests"], cwd=PDFIUM_DIR)


def test():
    # FlateModule.Encode may fail with older zlib (generates different results)
    os.environ["GTEST_FILTER"] = "*-FlateModule.Encode"
    pkgbase.run_cmd([PDFIUM_DIR/"out/Release"/"pdfium_unittests"], cwd=PDFIUM_DIR, check=False)


def main(build_ver=7049):
    full_ver = pkgbase.PdfiumVer.to_full(build_ver)
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    get_sources(full_ver)
    prepare(DefaultConfig)
    build()
    test()


if __name__ == "__main__":
    main()
