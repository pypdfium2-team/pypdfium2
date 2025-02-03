#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import shutil
import tarfile
import argparse
import functools
from pathlib import Path
import urllib.request as url_request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parents[1]))
from pypdfium2_setup.base import *


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
    
    fn = prefix + f"{PdfiumBinariesMap[pl_name]}.tgz"
    fu = f"{ReleaseURL}{version}/{fn}"
    fp = pl_dir / fn
    print(f"'{fu}' -> '{fp}'")
    
    try:
        url_request.urlretrieve(fu, fp)
    except Exception as e:
        if robust:
            print(str(e), file=sys.stderr)
            return None, None
        else:
            raise
    
    return pl_name, fp


def download(platforms, version, use_v8, max_workers, robust):
    
    if not max_workers:
        max_workers = len(platforms)
    
    archives = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        func = functools.partial(_get_package, version=version, robust=robust, use_v8=use_v8)
        for pl_name, file_path in pool.map(func, platforms):
            if pl_name is not None:
                archives[pl_name] = file_path
    
    return archives


def extract(archives, version, flags):
    
    for pl_name, arc_path in archives.items():
        
        with tarfile.open(arc_path) as tar:
            pl_dir = DataDir/pl_name
            system = plat_to_system(pl_name)
            libname = libname_for_system(system)
            tar_libdir = "lib" if system != SysNames.windows else "bin"
            tar_extract_file(tar, f"{tar_libdir}/{libname}", pl_dir/libname)
            write_pdfium_info(pl_dir, version, origin="pdfium-binaries", flags=flags)
        
        arc_path.unlink()


def postprocess_android(platforms):
    # see https://wiki.termux.com/wiki/FAQ#Why_does_a_compiled_program_show_warnings
    if Host.system == SysNames.android and Host.platform in platforms:
        elf_cleaner = shutil.which("termux-elf-cleaner")
        if elf_cleaner:
            print("Invoking termux-elf-cleaner to clean up possible linker warnings...", file=sys.stderr)
            libpath = DataDir / Host.platform / libname_for_system(Host.system)
            run_cmd([elf_cleaner, str(libpath)], cwd=None)
        else:
            print("If you are on Termux, consider installing termux-elf-cleaner to clean up possible linker warnings.", file=sys.stderr)


def main(platforms, version=None, robust=False, max_workers=None, use_v8=False):
    
    if not version:
        version = PdfiumVer.get_latest()
    if not platforms:
        platforms = WheelPlatforms
    if len(platforms) != len(set(platforms)):
        raise ValueError("Duplicate platforms not allowed.")
    
    flags = ["V8", "XFA"] if use_v8 else []
    
    clear_data(platforms)
    archives = download(platforms, version, use_v8, max_workers, robust)
    extract(archives, version, flags)
    postprocess_android(platforms)


# low-level CLI interface for testing - users should go with higher-level emplace.py or setup.py

def parse_args(argv):
    platform_choices = list(PdfiumBinariesMap.keys())
    parser = argparse.ArgumentParser(
        description = "Download pre-built PDFium packages.",
    )
    parser.add_argument(
        "--platforms", "-p",
        nargs = "+",
        metavar = "ID",
        choices = platform_choices,
        help = f"The platform(s) to include. Defaults to the platforms we build wheels for. Choices: {platform_choices}",
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
