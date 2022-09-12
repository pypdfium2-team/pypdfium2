#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Download the PDFium binaries and generate ctypes bindings

import os
import sys
import shutil
import tarfile
import argparse
import traceback
import functools
from urllib import request
from os.path import join, abspath, dirname
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from pl_setup.packaging_base import (
    DataTree,
    VerNamespace,
    ReleaseNames,
    BinaryPlatforms,
    ReleaseURL,
    AutoPlatformId,
    HostPlatform,
    set_version,
    get_latest_version,
    call_ctypesgen,
)


def handle_versions(latest):
    
    # TODO(#136@geisserml) Write version status file and handle the changes in `setup.py`.
    
    v_libpdfium = VerNamespace["V_LIBPDFIUM"]
    is_sourcebuild = VerNamespace["IS_SOURCEBUILD"]
    
    if is_sourcebuild:
        print("Switching from sourcebuild to pre-built binaries.")
        set_version("IS_SOURCEBUILD", False)
    if v_libpdfium != latest:
        set_version("V_LIBPDFIUM", latest)


def clear_data(download_files):
    for pl_name in download_files:
        pl_dir = join(DataTree, pl_name)
        if os.path.isdir(pl_dir):
            shutil.rmtree(pl_dir)


def _get_package(latest_ver, robust, pl_name):
    
    pl_dir = join(DataTree, pl_name)
    if not os.path.exists(pl_dir):
        os.makedirs(pl_dir)
    
    file_name = "%s.%s" % (ReleaseNames[pl_name], "tgz")
    file_url = "%s%s/%s" % (ReleaseURL, latest_ver, file_name)
    file_path = join(pl_dir, file_name)
    print("'%s' -> '%s'" % (file_url, file_path))
    
    try:
        request.urlretrieve(file_url, file_path)
    except Exception:
        if robust:
            traceback.print_exc()
            return None, None
        else:
            raise
    
    return pl_name, file_path


def download_releases(latest_ver, platforms, robust):
    archives = {}
    with ThreadPoolExecutor(max_workers=len(platforms)) as pool:
        func = functools.partial(_get_package, latest_ver, robust)
        for pl_name, file_path in pool.map(func, platforms):
            if pl_name is None:
                continue
            archives[pl_name] = file_path
    return archives


def unpack_archives(archives):
    for pl_name, file_path in archives.items():
        extraction_path = join(DataTree, pl_name, "build_tar")
        with tarfile.open(file_path) as archive:
            archive.extractall(extraction_path)
        os.remove(file_path)


def generate_bindings(archives):
    
    for pl_name in archives.keys():
        
        pl_dir = join(DataTree, pl_name)
        build_dir = join(pl_dir, "build_tar")
        bin_dir = join(build_dir, "lib")
        dirname = os.path.basename(pl_dir)
        
        if dirname.startswith("windows"):
            target_name = "pdfium.dll"
            bin_dir = join(build_dir, "bin")
        elif dirname.startswith("darwin"):
            target_name = "pdfium.dylib"
        elif "linux" in dirname:
            target_name = "pdfium"
        else:
            raise ValueError("Unknown platform directory name '%s'" % dirname)
        
        items = os.listdir(bin_dir)
        assert len(items) == 1
        
        shutil.move(join(bin_dir, items[0]), join(pl_dir, target_name))
        
        call_ctypesgen(pl_dir, join(build_dir, "include"))
        shutil.rmtree(build_dir)


def main(platforms, robust=False):
    
    if len(platforms) != len(set(platforms)):
        raise ValueError("Duplicate platforms not allowed.")
    if AutoPlatformId in platforms:
        platforms = platforms.copy()
        platforms[platforms.index(AutoPlatformId)] = HostPlatform().get_name()
    
    latest = get_latest_version()
    handle_versions(str(latest))
    clear_data(platforms)
    
    archives = download_releases(latest, platforms, robust)
    unpack_archives(archives)
    generate_bindings(archives)


def parse_args(argv):
    platform_choices = (AutoPlatformId, *BinaryPlatforms)
    parser = argparse.ArgumentParser(
        description = "Download pre-built PDFium packages and generate bindings.",
    )
    parser.add_argument(
        "--platforms", "-p",
        nargs = "+",
        metavar = "identifier",
        choices = platform_choices,
        default = BinaryPlatforms,
        help = "The platform(s) to include. Available platform identifiers are %s. `auto` represents the current host platform." % (platform_choices, ),
    )
    parser.add_argument(
        "--robust",
        action = "store_true",
        help = "Skip missing binaries instead of raising an exception.",
    )
    return parser.parse_args(argv)


def run_cli(argv=sys.argv[1:]):
    args = parse_args(argv)
    main(
        args.platforms,
        robust = args.robust,
    )


if __name__ == "__main__":
    run_cli()
