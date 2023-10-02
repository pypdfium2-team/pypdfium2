#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import shutil
import argparse
import traceback
import functools
from pathlib import Path
from urllib import request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parents[1]))
from pypdfium2_setup._compat import safer_tar_unpack
# TODO consider dotted access?
from pypdfium2_setup.packaging_base import *


def clear_data(download_files):
    for pl_name in download_files:
        pl_dir = DataDir / pl_name
        if pl_dir.exists():
            shutil.rmtree(pl_dir)


def _get_package(pl_name, version, robust, use_v8):
    
    pl_dir = DataDir / pl_name
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


# TODO Do not unpack whole archives, instead extract only the binaries we need and retrieve headers from pdfium directly. This would allow us to get rid of the tar compat code.

def unpack_archives(archives):
    for pl_name, archive_path in archives.items():
        dest_dir = DataDir / pl_name / "build_tar"
        safer_tar_unpack(archive_path, dest_dir)
        archive_path.unlink()


def generate_bindings(archives, version, use_v8, ctypesgen_kws):
    
    flags = []
    if use_v8:
        flags += ["V8", "XFA"]
    
    for pl_name in archives.keys():
        
        pl_dir = DataDir / pl_name
        build_dir = pl_dir / "build_tar"
        bin_dir = build_dir / "lib"
        
        system = plat_to_system(pl_name)
        if system == SysNames.windows:
            bin_dir = build_dir / "bin"
        
        libname = LibnameForSystem[system]
        src_libpath = bin_dir / libname
        assert src_libpath.is_file()
        shutil.copyfile(src_libpath, pl_dir/libname)
        
        call_ctypesgen(pl_dir, build_dir/"include", pl_name=pl_name, use_v8xfa=use_v8, **ctypesgen_kws)
        write_pdfium_info(DataDir/pl_name, version=version, origin="pdfium-binaries", flags=flags)
        
        shutil.rmtree(build_dir)


def main(platforms, version=None, robust=False, max_workers=None, use_v8=False, ctypesgen_kws={}):
    
    if not version:
        version = PdfiumVer.get_latest()
    if not platforms:
        platforms = BinaryPlatforms
    if len(platforms) != len(set(platforms)):
        raise ValueError("Duplicate platforms not allowed.")
    
    clear_data(platforms)
    archives = download_releases(platforms, version, use_v8, max_workers, robust)
    unpack_archives(archives)
    generate_bindings(archives, version, use_v8, ctypesgen_kws)


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
        help = "Use V8 binaries (JavaScript/XFA support)."
    )
    parser.add_argument(
        "--version", "-v",
        type = int,
        help = "The binaries release to use (defaults to latest). Must be a valid tag integer."
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
