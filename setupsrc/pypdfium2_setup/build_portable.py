#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import re
import sys
from pathlib import Path
from urllib.request import urlretrieve
from functools import cached_property

sys.path.insert(0, str(Path(__file__).parents[1]))
import pypdfium2_setup.base as pkgbase

_CHROMIUM_URL = "https://chromium.googlesource.com/"
PDFIUM_URL = "https://pdfium.googlesource.com/pdfium/+archive/refs/heads/chromium/{short_ver}.tar.gz#/pdfium-{short_ver}.tar.gz"
DEPS_URLS = dict(
    build = _CHROMIUM_URL + "chromium/src/build.git/+archive/{rev}.tar.gz#/build-{rev}.tar.gz",
    abseil = _CHROMIUM_URL + "chromium/src/third_party/abseil-cpp/+archive/{rev}.tar.gz#/abseil-cpp-{rev}.tar.gz",
    fast_float = _CHROMIUM_URL + "external/github.com/fastfloat/fast_float.git/+archive/{rev}.tar.gz#/fast_float-{rev}.tar.gz",
    gtest = _CHROMIUM_URL + "external/github.com/google/googletest.git/+archive/{rev}.tar.gz#/gtest-{rev}.tar.gz",
    test_fonts = _CHROMIUM_URL + "chromium/src/third_party/test_fonts.git/+archive/{rev}.tar.gz#/test_fonts-{rev}.tar.gz"
)
SHIMHEADERS_URL = _CHROMIUM_URL + "chromium/src/+archive/refs/tags/{full_ver}/tools/generate_shim_headers.tar.gz#/generate_shim_headers-{full_ver}.tar.gz"

SOURCES_DIR = pkgbase.ProjectDir / "sourcebuild_lean"
PDFIUM_DIR = SOURCES_DIR/"pdfium"


# tar unpacking template from https://gist.github.com/mara004/6fe0ac15d0cf303bed0aea2f22d8531f

import sys
if sys.version_info >= (3, 11, 4):  # PEP 706
    import shutil
    def safer_tar_unpack(archive_path, dest_dir):
        shutil.unpack_archive(archive_path, dest_dir, format="tar", filter="data")

else:  # workaround
    import tarfile
    from pathlib import Path
    
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
    else:
        print(f"Using existing {archive_path}")
    
    print(f"Unpacking {archive_url!r} to {dest_path} ...")
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
        print(f"Found DEPS revisions:\n{result}", file=sys.stderr)
        return result

_Deferred = _DeferredClass()


def _fetch_dep(name, target_dir):
    if target_dir.exists():
        print(f"Using existing {target_dir}")
        return False
    # parse out DEPS revisions only if we actually need them
    return _fetch_archive(DEPS_URLS[name].format(rev=_Deferred.deps[name]), target_dir)

def apply_patch(patch, cwd):
    # FIXME portability?
    pkgbase.git_apply_patch(patch, cwd, git_args=("--git-dir=/dev/null", "--work-tree=."))


def get_sources(version):
    
    # TODO consider cloning the main pdfium from git?
    
    version_str = ".".join(str(v) for v in version)
    SOURCES_DIR.mkdir(exist_ok=True)
    
    is_new = _fetch_archive(PDFIUM_URL.format(short_ver=version.build), PDFIUM_DIR)
    if is_new:
        print("Applying pdfium patches ...")
        apply_patch(pkgbase.PatchDir/"public_headers.patch", PDFIUM_DIR)
    
    _fetch_dep("build", PDFIUM_DIR/"build")
    _fetch_dep("abseil", PDFIUM_DIR/"third_party"/"abseil-cpp")
    _fetch_dep("fast_float", PDFIUM_DIR/"third_party"/"fast_float"/"src")
    _fetch_dep("gtest", PDFIUM_DIR/"third_party"/"googletest"/"src")
    _fetch_dep("test_fonts", PDFIUM_DIR/"third_party"/"test_fonts")
    _fetch_archive(SHIMHEADERS_URL.format(full_ver=version_str), PDFIUM_DIR/"tools"/"generate_shim_headers")


def main():
    version = pkgbase.PdfiumVer.scheme(135, 0, 7049, 0)
    get_sources(version)


if __name__ == "__main__":
    main()
