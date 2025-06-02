#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# NOTE: unless otherwise noted, "version" refers to the short version in this file

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
    mkdir(pl_dir)
    
    prefix = "pdfium-"
    if use_v8:
        prefix += "v8-"
    
    fn = prefix + f"{PdfiumBinariesMap[pl_name]}.tgz"
    fu = f"{ReleaseURL}{version}/{fn}"
    fp = pl_dir / fn
    log(f"'{fu}' -> '{fp}'")
    
    try:
        url_request.urlretrieve(fu, fp)
    except Exception as e:
        if robust:
            log(str(e))
            return None, None
        else:
            raise
    
    return pl_name, fp


def do_download(platforms, version, use_v8, max_workers, robust):
    
    if not max_workers:
        max_workers = len(platforms)
    
    archives = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        func = functools.partial(_get_package, version=version, robust=robust, use_v8=use_v8)
        for pl_name, file_path in pool.map(func, platforms):
            if pl_name is not None:
                archives[pl_name] = file_path
    
    return archives


def _parse_ver_file(buffer, short_ver):
    content = buffer.read().decode().strip()
    full_ver = [int(l.split("=")[-1].strip()) for l in content.split("\n")]
    full_ver = PdfiumVer.scheme(*full_ver)
    assert full_ver.build == short_ver
    if full_ver in PdfiumVer._vdict:
        assert PdfiumVer._vdict[short_ver] == full_ver
    else:
        PdfiumVer._vdict[full_ver.build] = full_ver
    log(f"Resolved {short_ver} -> {full_ver} (by pdfium-binaries VERSION)")
    return full_ver


def _extract_licenses(tar, pl_dir):
    licenses_dir = pl_dir/"BUILD_LICENSES"
    mkdir(licenses_dir)
    all_paths = tar.getnames()
    if "licenses" in all_paths:
        license_paths = (p for p in all_paths if p.startswith("licenses/"))
        for path in license_paths:
            tar_extract_file(tar, path, licenses_dir/Path(path).name)
        tar_extract_file(tar, "LICENSE", licenses_dir/"pdfium-binaries.txt")
    else:
        # backwards compat with pdfium-binaries < 7175
        tar_extract_file(tar, "LICENSE", licenses_dir/"aggregated-license.txt")


def do_extract(archives, version, flags):
    
    for pl_name, arc_path in archives.items():
        
        with tarfile.open(arc_path) as tar:
            pl_dir = DataDir/pl_name
            system = plat_to_system(pl_name)
            libname = libname_for_system(system)
            tar_libdir = "lib" if system != SysNames.windows else "bin"
            tar_extract_file(tar, f"{tar_libdir}/{libname}", pl_dir/libname)
            _extract_licenses(tar, pl_dir)
            full_ver = _parse_ver_file(tar.extractfile("VERSION"), version)
            write_pdfium_info(pl_dir, full_ver, origin="pdfium-binaries", flags=flags)
        
        arc_path.unlink()


def do_verify(archives, version):
    # TODO rename to pdfium-binaries.intoto.jsonl once upstream does
    ProvenanceFile = DataDir/"multiple.intoto.jsonl"
    ProvenanceFile.unlink(missing_ok=True)
    url_request.urlretrieve(f"{ReleaseURL}{version}/{ProvenanceFile.name}", ProvenanceFile)
    artifact_paths = [str(p) for p in archives.values()]
    cmd = [
        "slsa-verifier",
        "verify-artifact", *artifact_paths,
        "--provenance-path", str(ProvenanceFile),
        "--source-uri", "github.com/bblanchon/pdfium-binaries",
    ]
    log("\n-- Start slsa-verify --")
    run_cmd(cmd, cwd=DataDir, check=True)
    log("-- End slsa-verify --\n")


def postprocess_android(platforms):
    # see https://wiki.termux.com/wiki/FAQ#Why_does_a_compiled_program_show_warnings
    if not (Host.system == SysNames.android and Host.platform in platforms):
        return
    elf_cleaner = shutil.which("termux-elf-cleaner")
    if elf_cleaner:
        log("Invoking termux-elf-cleaner to clean up possible linker warnings...")
        libpath = DataDir / Host.platform / libname_for_system(Host.system)
        run_cmd([elf_cleaner, str(libpath)], cwd=None)
    else:
        log("If you are on Termux, consider installing termux-elf-cleaner to clean up possible linker warnings.")


def main(platforms, version=None, robust=False, max_workers=None, use_v8=False, verify=None):
    
    if not version:
        version = PdfiumVer.get_latest()
    if not platforms:
        platforms = WheelPlatforms
    if verify is None:
        verify = bool(shutil.which("slsa-verifier"))
    if len(platforms) != len(set(platforms)):
        raise ValueError("Duplicate platforms not allowed.")
    
    flags = ("V8", "XFA") if use_v8 else ()
    
    clear_data(platforms)
    archives = do_download(platforms, version, use_v8, max_workers, robust)
    if verify:
        do_verify(archives, version)
    else:
        log("Warning: Verification is off - this is unsafe! If this is not intentional, make sure slsa-verifier is installed.")
    do_extract(archives, version, flags)
    postprocess_android(platforms)


# low-level interface for internal use - end users should go with cached, higher-level emplace.py or setup.py instead

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
    parser.add_argument(
        "--verify",
        action = "store_true",
        default = None,
        help = "Verify release artifacts via SLSA provenance. This will be automatically enabled if slsa-verifier is installed.",
    )
    return parser.parse_args(argv)


def cli_main(argv=sys.argv[1:]):
    args = parse_args(argv)
    main(**vars(args))


if __name__ == "__main__":
    cli_main()
