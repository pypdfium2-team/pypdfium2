#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from pypdfium2_setup import update_pdfium
from pypdfium2_setup.packaging_base import (
    # CONSIDER glob import or dotted access
    Host,
    DataTree,
    BinarySpec_EnvVar,
    BinarySpec_VersionSep,
    BinarySpec_V8Indicator,
    PlatformTarget_Auto,
    PlatformTarget_None,
    VersionTarget_Latest,
    VerStatusFileName,
    V8StatusFileName,
    PlatformNames,
    get_platfiles,
    clean_platfiles,
    emplace_platfiles,
    get_latest_version,
    read_version_file,
    purge_pdfium_versions,
)


# CONSIDER Linux/macOS: check that minimum OS version requirements are fulfilled
# TODO add direct support for emplacing local pdfium from file


def get_pdfium(binary_spec, force_rebuild=False):
    
    if binary_spec == PlatformNames.sourcebuild:
        # for now, require that callers ran build_pdfium.py beforehand so they are in charge of the build config - don't trigger sourcebuild in here if platform files don't exist
        return PlatformNames.sourcebuild
    
    req_ver = None
    use_v8 = False
    if BinarySpec_VersionSep in binary_spec:
        binary_spec, req_ver = binary_spec.rsplit(BinarySpec_VersionSep)
    if binary_spec.endswith(BinarySpec_V8Indicator):
        binary_spec = binary_spec.rstrip(BinarySpec_V8Indicator)  # should be removesuffix() (pep616, python>=3.9)
        use_v8 = True
    
    if not binary_spec or binary_spec.lower() == PlatformTarget_Auto:
        pl_name = Host.platform
        if pl_name is None:
            raise RuntimeError(f"No pre-built binaries available for system {Host._system_name} (libc info {Host._libc_info}) on machine {Host._machine_name}. You may place custom binaries & bindings in data/sourcebuild and install with `{BinarySpec_EnvVar}=sourcebuild`.")
    elif hasattr(PlatformNames, binary_spec):
        pl_name = getattr(PlatformNames, binary_spec)
    else:
        raise ValueError(f"Invalid binary spec '{binary_spec}'")
    
    if not req_ver or (req_ver.lower() == VersionTarget_Latest):
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
    
    need_rebuild = (prev_ver != req_ver or had_v8 != use_v8)
    if need_rebuild or force_rebuild:
        if need_rebuild:
            print(f"Switching pdfium binary from ({prev_ver}, v8 {had_v8}) to ({req_ver}, v8 {use_v8})", file=sys.stderr)
        else:  # force_rebuild
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
        "binary_spec",
        type = str.strip,
        default = os.environ.get(BinarySpec_EnvVar, ""),
        nargs = "?",
        help = f"The binary specifier. Same format as of ${BinarySpec_EnvVar} on setup.",
    )
    parser.add_argument(
        "--force-rebuild", "-f",
        action = "store_true",
        help = "If given, always rebuild platform files even if a matching cache exists already.",
    )
    args = parser.parse_args()
    
    if args.binary_spec == PlatformTarget_None:
        print("Removing existing in-tree platform files, if any.", file=sys.stderr)
        clean_platfiles()
        purge_pdfium_versions()
        return
    
    pl_name = get_pdfium(args.binary_spec, args.force_rebuild)
    emplace_platfiles(pl_name)


if __name__ == "__main__":
    main()
