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
# FIXME V8 integration is a bit polluted (flags vs. bool)


def _repr_info(version, flags):
    return str(version) + (":{%s}" % ','.join(flags) if flags else "")


def get_pdfium(plat_spec, force_rebuild=False):
    
    if plat_spec == PlatNames.sourcebuild:
        # for now, require that callers ran build_pdfium.py beforehand so they are in charge of the build config - don't trigger sourcebuild in here if platform files don't exist
        return PlatNames.sourcebuild
    
    req_ver = None
    req_flags = []
    use_v8 = False
    if PlatSpec_VerSep in plat_spec:
        plat_spec, req_ver = plat_spec.rsplit(PlatSpec_VerSep)
    if plat_spec.endswith(PlatSpec_V8Sym):
        plat_spec = plat_spec[:-len(PlatSpec_V8Sym)]
        req_flags += ["V8", "XFA"]
        use_v8 = True
    
    if not plat_spec or plat_spec.lower() == PlatTarget_Auto:
        pl_name = Host.platform
        if pl_name is None:
            raise RuntimeError(f"No pre-built binaries available for {Host}. You may place custom binaries & bindings in data/sourcebuild and install with `{PlatSpec_EnvVar}=sourcebuild`.")
    elif hasattr(PlatNames, plat_spec):
        pl_name = getattr(PlatNames, plat_spec)
    else:
        raise ValueError(f"Invalid binary spec '{plat_spec}'")
    
    if not req_ver or req_ver.lower() == VerTarget_Latest:
        req_ver = PdfiumVer.get_latest()
    else:
        assert req_ver.isnumeric()
        req_ver = int(req_ver)
    
    prev_repr = "(Unknown)"
    if force_rebuild:
        need_rebuild = True
        prev_repr = "(Ignored)"
    else:
        pl_dir = DataDir / pl_name
        ver_file = pl_dir / VersionFN
        if ver_file.exists() and all(fp.exists() for fp in get_platfiles(pl_name)):
            prev_info = read_json(ver_file)
            need_rebuild = prev_info["build"] != req_ver or set(prev_info["flags"]) != set(req_flags)
            prev_repr = _repr_info(prev_info["build"], prev_info["flags"])
        else:
            need_rebuild = True
    
    req_repr = _repr_info(req_ver, req_flags)
    
    if need_rebuild:
        print(f"Switch from pdfium {prev_repr} to {req_repr}", file=sys.stderr)
        update_pdfium.main([pl_name], version=req_ver, use_v8=use_v8)
    else:
        print(f"Use existing cache for pdfium {req_repr}", file=sys.stderr)
    
    return pl_name


def main():
    
    parser = argparse.ArgumentParser(
        description = "Manage in-tree artifacts from an editable install.",
    )
    parser.add_argument(
        "plat_spec",
        default = os.environ.get(PlatSpec_EnvVar, ""),
        nargs = "?",
        help = f"The platform specifier. Same format as of ${PlatSpec_EnvVar} on setup. 'none' removes existing artifacts.",
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
        return
    
    pl_name = get_pdfium(args.plat_spec, args.force_rebuild)
    emplace_platfiles(pl_name)


if __name__ == "__main__":
    main()
