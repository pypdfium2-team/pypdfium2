#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import os.path
import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from pypdfium2_setup.base import *
from pypdfium2_setup import update as update_pdfium


def _repr_info(version, flags):
    return str(version) + (f":{','.join(flags)}" if flags else "")

def _get_pdfium_with_cache(pl_name, req_ver, req_flags, use_v8):
    
    system = plat_to_system(pl_name)
    pl_dir = DataDir / pl_name
    binary = pl_dir / libname_for_system(system)
    binary_ver = pl_dir / VersionFN
    
    if all(f.exists() for f in (binary, binary_ver)):
        prev_info = read_json(binary_ver)
        update_binary = prev_info["build"] != req_ver or set(prev_info["flags"]) != set(req_flags)
    else:
        update_binary = True
    
    req_repr = _repr_info(req_ver, req_flags)
    if update_binary:
        print(f"Downloading binary {req_repr} ...", file=sys.stderr)
        update_pdfium.main([pl_name], version=req_ver, use_v8=use_v8)
    else:
        print(f"Using cached binary {req_repr}")
    
    # build_pdfium_bindings() has its own cache logic, so always call to ensure bindings match
    compile_lds = [DataDir/Host.platform] if pl_name == Host.platform else []
    build_pdfium_bindings(req_ver, flags=req_flags, compile_lds=compile_lds)


def prepare_setup(pl_name, pdfium_ver, use_v8):
    
    clean_platfiles()
    flags = ["V8", "XFA"] if use_v8 else []
    
    # TODO for PDFIUM_PLATFORM=system, add option for caller to pass in custom headers_dir, run_lds and flags? this might cause more fragmentation, though
    # also want to consider accepting a full version for offline setup
    
    if pl_name == ExtPlats.system:
        build_pdfium_bindings(pdfium_ver, flags=flags, guard_symbols=True, run_lds=())
        shutil.copyfile(DataDir_Bindings/BindingsFN, ModuleDir_Raw/BindingsFN)
        write_pdfium_info(ModuleDir_Raw, pdfium_ver, origin="system", flags=flags)
        return [BindingsFN, VersionFN]
    
    else:
        
        platfiles = []
        pl_dir = DataDir/pl_name
        system = plat_to_system(pl_name)
        
        if pl_name == ExtPlats.sourcebuild:
            # sourcebuild bindings are kept in the platform directory
            platfiles += [pl_dir/BindingsFN]
        else:
            platfiles += [DataDir_Bindings/BindingsFN]
            _get_pdfium_with_cache(pl_name, pdfium_ver, flags, use_v8)
        
        platfiles += [pl_dir/libname_for_system(system), pl_dir/VersionFN]
        for fp in platfiles:
            shutil.copyfile(fp, ModuleDir_Raw/fp.name)
        
        return [fp.name for fp in platfiles]


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
    args = parser.parse_args()
    
    if args.plat_spec == ExtPlats.sdist:
        print("Remove existing in-tree platform files, if any.", file=sys.stderr)
        clean_platfiles()
        return
    
    parsed_spec = parse_pl_spec(args.plat_spec)
    if parsed_spec is None:
        raise Host._exc
    do_prepare, *pl_info = parsed_spec
    assert do_prepare, "Can't use already-prepared target with emplace, would be no-op."
    prepare_setup(*pl_info)


if __name__ == "__main__":
    main()
