#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from pypdfium2_setup import update_pdfium
# TODO consider dotted access?
from pypdfium2_setup.packaging_base import *


# CONSIDER Linux/macOS: check that minimum OS version requirements are fulfilled
# TODO add direct support for emplacing local pdfium from file


def get_pdfium(plat_spec, force_rebuild=False):
    
    if plat_spec == PlatNames.sourcebuild:
        # for now, require that callers ran build_pdfium.py beforehand so they are in charge of the build config - don't trigger sourcebuild in here if platform files don't exist
        return PlatNames.sourcebuild
    
    req_ver = None
    use_v8 = False
    if PlatSpec_VerSep in plat_spec:
        plat_spec, req_ver = plat_spec.rsplit(PlatSpec_VerSep)
    if plat_spec.endswith(PlatSpec_V8Sym):
        plat_spec = plat_spec.rstrip(PlatSpec_V8Sym)  # should be removesuffix() (pep616, python>=3.9)
        use_v8 = True
    
    if not plat_spec or plat_spec.lower() == PlatTarget_Auto:
        pl_name = Host.platform
        if pl_name is None:
            raise RuntimeError(f"No pre-built binaries available for system {Host._system_name} (libc info {Host._libc_info}) on machine {Host._machine_name}. You may place custom binaries & bindings in data/sourcebuild and install with `{PlatSpec_EnvVar}=sourcebuild`.")
    elif hasattr(PlatNames, plat_spec):
        pl_name = getattr(PlatNames, plat_spec)
    else:
        raise ValueError(f"Invalid binary spec '{plat_spec}'")
    
    if not req_ver or req_ver.lower() == VerTarget_Latest:
        req_ver = get_latest_version()
    else:
        assert req_ver.isnumeric()
        req_ver = int(req_ver)
    
    pl_dir = DataTree / pl_name
    ver_file = pl_dir / VerStatusFileName
    had_v8 = (pl_dir / V8StatusFileName).exists()
    prev_ver = None
    if ver_file.exists() and all(fp.exists() for fp in get_platfiles(pl_name)):
        prev_ver = int( read_version_file(ver_file)[0] )
    
    need_rebuild = prev_ver != req_ver or had_v8 != use_v8
    if need_rebuild or force_rebuild:
        if need_rebuild:
            print(f"Switching pdfium binary from ({prev_ver}, v8 {had_v8}) to ({req_ver}, v8 {use_v8})", file=sys.stderr)
        else:
            print(f"Force-rebuild ({req_ver}, v8 {use_v8}) despite cache", file=sys.stderr)
        # NOTE update_pdfium cleans up pl_dir for us in case of mismatched existing cache
        update_pdfium.main([pl_name], version=req_ver, use_v8=use_v8)
    else:
        print(f"Matching pdfium binary/bindings exists already ({req_ver}, v8 {use_v8})", file=sys.stderr)
    
    return pl_name


def main():
    
    parser = argparse.ArgumentParser(
        description = "Manage in-tree artifacts from an editable install.",
    )
    parser.add_argument(
        "plat_spec",
        default = os.environ.get(PlatSpec_EnvVar, ""),
        nargs = "?",
        help = f"The platform specifier. Same format as of ${PlatSpec_EnvVar} on setup, except that 'none' removes existing artifacts.",
    )
    parser.add_argument(
        "--force-rebuild", "-f",
        action = "store_true",
        help = "If given, always rebuild platform files even if a matching cache exists already.",
    )
    args = parser.parse_args()
    
    if args.plat_spec == PlatTarget_None:
        print("Remove existing in-tree platform files, if any.", file=sys.stderr)
        clean_platfiles()
        purge_pdfium_versions()
        return
    
    pl_name = get_pdfium(args.plat_spec, args.force_rebuild)
    emplace_platfiles(pl_name)


if __name__ == "__main__":
    main()
