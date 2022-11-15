#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import shutil
import tarfile
import argparse
import traceback
import functools
import os.path
from os.path import join, abspath, dirname
from urllib import request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from pl_setup.packaging_base import (
    Host,
    DataTree,
    VerStatusFileName,
    ReleaseNames,
    BinaryPlatforms,
    ReleaseURL,
    BinaryTarget_Auto,
    get_latest_version,
    call_ctypesgen,
)


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


def download_releases(latest_ver, platforms, robust, max_workers):
    if not max_workers:
        max_workers = len(platforms)
    archives = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        func = functools.partial(_get_package, latest_ver, robust)
        for pl_name, file_path in pool.map(func, platforms):
            if pl_name is None:
                continue
            archives[pl_name] = file_path
    return archives


# Tar extraction helpers to prevent CVE-2007-4559 (path traversal attack) - Thanks to @Kasimir123 and @TrellixVulnTeam
# To the author's knowledge, Python's standard library does not provide a function to extract tars safely
# (It has been reported that shutil.unpack_archive() is affected by the vulnerability as well.)

def _is_within_dir(directory, target):
    abs_directory = abspath(directory)
    abs_target = abspath(target)
    prefix = os.path.commonprefix([abs_directory, abs_target])
    return prefix == abs_directory

def safe_extract(tar, path=".", **kwargs):
    for member in tar.getmembers():
        member_path = join(path, member.name)
        if not _is_within_dir(path, member_path):
            raise RuntimeError("Attempted path traversal in tar archive (probably malicious).")
    tar.extractall(path, **kwargs)


def unpack_archives(archives):
    for pl_name, file_path in archives.items():
        dest_path = join(DataTree, pl_name, "build_tar")
        with tarfile.open(file_path) as archive:
            safe_extract(archive, dest_path)
        os.remove(file_path)


def generate_bindings(archives, latest_ver):
    
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
        
        ver_file = join(DataTree, pl_name, VerStatusFileName)
        with open(ver_file, "w") as fh:
            fh.write(latest_ver)
        
        call_ctypesgen(pl_dir, join(build_dir, "include"))
        shutil.rmtree(build_dir)


def main(platforms, robust=False, max_workers=None):
    
    if len(platforms) != len(set(platforms)):
        raise ValueError("Duplicate platforms not allowed.")
    if BinaryTarget_Auto in platforms:
        platforms = platforms.copy()
        platforms[platforms.index(BinaryTarget_Auto)] = Host.platform
    
    latest_ver = str( get_latest_version() )
    clear_data(platforms)
    
    archives = download_releases(latest_ver, platforms, robust, max_workers)
    unpack_archives(archives)
    generate_bindings(archives, latest_ver)


def parse_args(argv):
    platform_choices = (BinaryTarget_Auto, *BinaryPlatforms)
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
    parser.add_argument(
        "--max-workers",
        type = int,
        help = "Maximum number of jobs to run in parallel when downloading binaries.",
    )
    return parser.parse_args(argv)


def run_cli(argv=sys.argv[1:]):
    args = parse_args(argv)
    main(
        args.platforms,
        robust = args.robust,
        max_workers = args.max_workers,
    )


if __name__ == "__main__":
    run_cli()
