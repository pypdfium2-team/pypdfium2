#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import shutil
import tarfile
import argparse
import traceback
import functools
import os.path
from pathlib import Path
from urllib import request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parents[1]))
# CONSIDER glob import or dotted access
from pypdfium2_setup.packaging_base import (
    DataTree,
    VerStatusFileName,
    V8StatusFileName,
    ReleaseNames,
    BinaryPlatforms,
    ReleaseURL,
    get_latest_version,
    call_ctypesgen,
)


def clear_data(download_files):
    for pl_name in download_files:
        pl_dir = DataTree / pl_name
        if pl_dir.exists():
            shutil.rmtree(pl_dir)


def _get_package(pl_name, version, robust, use_v8):
    
    pl_dir = DataTree / pl_name
    pl_dir.mkdir(parents=True, exist_ok=True)
    
    prefix = "pdfium-"
    if use_v8:
        prefix += "v8-"
    
    fn = prefix + f"{ReleaseNames[pl_name]}.tgz"
    fu = f"{ReleaseURL}{version}/{fn}"
    fp = pl_dir / fn
    print(f"'{fu}' -> '{fp}'")
    
    try:
        request.urlretrieve(fu, fp)
    except Exception:
        if robust:
            traceback.print_exc()
            return None, None
        else:
            raise
    
    if use_v8:
        (pl_dir / V8StatusFileName).touch(exist_ok=True)
    
    return pl_name, fp


def download_releases(platforms, version, use_v8, max_workers, robust):
    
    if not max_workers:
        max_workers = len(platforms)
    
    archives = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        func = functools.partial(_get_package, version=version, robust=robust, use_v8=use_v8)
        for pl_name, file_path in pool.map(func, platforms):
            if pl_name is not None:
                archives[pl_name] = file_path
    
    return archives


def safe_extract(tar, dest_dir, **kwargs):
    
    # Workaround against CVE-2007-4559 (path traversal attack) (thanks @Kasimir123 / @TrellixVulnTeam)
    # Actually, we would just like to use shutil.unpack_archive() or similar, but to the author's knowledge, the stdlib still does not provide any (simple) means to extract tars safely (as of Feb 2023).
    # It is not understandable why they don't just add an option `prevent_traversal` or something to shutil.unpack_archive().
    
    dest_dir = dest_dir.resolve()
    for member in tar.getmembers():
        # if not (dest_dir/member.name).resolve().is_relative_to(dest_dir):  # python >= 3.9
        if str(dest_dir) != os.path.commonpath( [dest_dir, (dest_dir/member.name).resolve()] ):
            raise RuntimeError("Attempted path traversal in tar archive (probably malicious).")
    tar.extractall(dest_dir, **kwargs)


def unpack_archives(archives):
    for pl_name, fp in archives.items():
        dest_dir = DataTree / pl_name / "build_tar"
        with tarfile.open(fp) as archive:
            safe_extract(archive, dest_dir)
        fp.unlink()


def generate_bindings(archives, version):
    
    for pl_name in archives.keys():
        
        pl_dir = DataTree / pl_name
        build_dir = pl_dir / "build_tar"
        bin_dir = build_dir / "lib"
        dirname = pl_dir.name
        
        if dirname.startswith("windows"):
            target_name = "pdfium.dll"
            bin_dir = build_dir / "bin"
        elif dirname.startswith("darwin"):
            target_name = "pdfium.dylib"
        elif "linux" in dirname:
            target_name = "pdfium"
        else:
            raise ValueError(f"Unknown platform directory name '{dirname}'")
        
        items = list(bin_dir.iterdir())
        assert len(items) == 1
        shutil.move(bin_dir/items[0], pl_dir/target_name)
        
        ver_file = DataTree / pl_name / VerStatusFileName
        ver_file.write_text(str(version))
        
        call_ctypesgen(pl_dir, build_dir/"include")
        shutil.rmtree(build_dir)


def main(platforms, version=None, robust=False, max_workers=None, use_v8=False):
    
    if not version:
        version = get_latest_version()
    if not platforms:
        platforms = BinaryPlatforms
    if len(platforms) != len(set(platforms)):
        raise ValueError("Duplicate platforms not allowed.")

    clear_data(platforms)
    archives = download_releases(platforms, version, use_v8, max_workers, robust)
    unpack_archives(archives)
    generate_bindings(archives, version)


# low-level CLI interface for testing - users should go with higher-level emplace.py or setup.py

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description = "Download pre-built PDFium packages and generate bindings.",
    )
    parser.add_argument(
        # FIXME with metavar, choices are not visible in help by default - without it, the long choices list is repeated 4 times due to 2 flags and nargs="+"
        "--platforms", "-p",
        nargs = "+",
        metavar = "ID",
        choices = BinaryPlatforms,
        help = f"The platform(s) to include. Choices: {BinaryPlatforms}",
    )
    parser.add_argument(
        "--use-v8",
        action = "store_true",
        help = "Use PDFium V8 binaries for JavaScript and XFA support."
    )
    parser.add_argument(
        "--version", "-v",
        type = int,
        help = "The pdfium-binaries release to use (defaults to latest). Must be a valid tag integer."
    )
    parser.add_argument(
        "--max-workers",
        type = int,
        help = "Maximum number of jobs to run in parallel when downloading binaries.",
    )
    parser.add_argument(
        "--robust",
        action = "store_true",
        help = "Skip missing binaries instead of raising an exception.",
    )
    return parser.parse_args(argv)


def cli_main(argv=sys.argv[1:]):
    main( **vars( parse_args(argv) ) )


if __name__ == "__main__":
    cli_main()
