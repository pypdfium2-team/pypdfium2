#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import shutil
import tarfile
import argparse
import traceback
import functools
from pathlib import Path
from urllib import request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parents[1]))
from pypdfium2_setup.packaging_base import (
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
        pl_dir = DataTree / pl_name
        if pl_dir.exists():
            shutil.rmtree(pl_dir)


def _get_package(latest_ver, robust, pl_name):
    
    pl_dir = DataTree / pl_name
    pl_dir.mkdir(parents=True, exist_ok=True)
    
    fn = f"{ReleaseNames[pl_name]}.tgz"
    fu = f"{ReleaseURL}{latest_ver}/{fn}"
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
    
    return pl_name, fp


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



def safe_extract(tar, dest_dir, **kwargs):
    
    # Workaround against CVE-2007-4559 (path traversal attack) (thanks @Kasimir123 / @TrellixVulnTeam)
    # Actually, we would just like to use shutil.unpack_archive() or similar, but to the author's knowledge, the stdlib still does not provide any (simple) means to extract tars safely (as of Feb 2023).
    # It is not understandable why they don't just add an option `prevent_traversal` or something to shutil.unpack_archive().
    
    dest_dir = dest_dir.resolve()
    for member in tar.getmembers():
        # if str(dest_dir) != os.path.commonprefix( [dest_dir, (dest_dir/member.name).resolve()] ):
        # ^ initial @Kasimir123/@TrellixVulnTeam logic, simplified into a one-liner; code below should have same effect
        # (yes, this also works against absolute paths)
        # if not (dest_dir/member.name).resolve().is_relative_to(dest_dir):  # python >= 3.9
        if not str( (dest_dir/member.name).resolve() ).startswith( str(dest_dir) ):
            raise RuntimeError("Attempted path traversal in tar archive (probably malicious).")
    tar.extractall(dest_dir, **kwargs)


def unpack_archives(archives):
    for pl_name, fp in archives.items():
        dest_dir = DataTree / pl_name / "build_tar"
        with tarfile.open(fp) as archive:
            safe_extract(archive, dest_dir)
        fp.unlink()


def generate_bindings(archives, latest_ver):
    
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
        shutil.move(bin_dir / items[0], pl_dir / target_name)
        
        ver_file = DataTree / pl_name / VerStatusFileName
        ver_file.write_text(latest_ver)
        
        call_ctypesgen(pl_dir, build_dir/"include")
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
        help = f"The platform(s) to include. `auto` represents the current host platform. Choices: {platform_choices}.",
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
