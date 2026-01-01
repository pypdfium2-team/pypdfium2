#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import shlex
import argparse
import traceback

# local
from base import *
import update as update_pdfium
import build_native
import build_toolchained
import system_pdfium


def _repr_info(version, flags):
    return str(version) + (f":{','.join(flags)}" if flags else "")

def _get_pdfium_with_cache(pl_name, req_ver, req_flags):
    
    # TODO turn platform and system into proper objects, so the libname could be accessed like plat.system.libname, which is much cleaner than a chain of string function calls
    
    pl_dir = DataDir/pl_name
    system = plat_to_system(pl_name)
    binary = pl_dir/libname_for_system(system)
    binary_ver = pl_dir/VersionFN
    
    if all(f.exists() for f in (binary, binary_ver)):
        prev_info = read_json(binary_ver)
        update_binary = prev_info["build"] != req_ver or set(prev_info["flags"]) != set(req_flags)
    else:
        update_binary = True
    
    req_repr = _repr_info(req_ver, req_flags)
    if update_binary:
        log(f"Downloading binary {req_repr} ...")
        update_pdfium.main([pl_name], version=req_ver, use_v8=("V8" in req_flags))
    else:
        log(f"Using cached binary {req_repr}")
    
    # build_pdfium_bindings() has its own cache logic, so always call to ensure bindings match
    ct_paths = (DataDir/Host.platform/CTG_LIBPATTERN, ) if pl_name == Host.platform else ()
    build_pdfium_bindings(req_ver, flags=req_flags, ct_paths=ct_paths)

def _end_subtargets(sub_target, pdfium_ver):
    if sub_target:
        assert False, sub_target
    else:
        log("No sub-target set, will use existing data files.")
        if pdfium_ver:
            raise ValueError(f"Pdfium version {pdfium_ver} was passed, but this does not make sense with caller-provided data files.")


def stage_platfiles(pl_name, sub_target, pdfium_ver, flags, default_build_params=""):
    
    if pl_name == ExtPlats.system:
        pl_dir = DataDir/pl_name
        if sub_target:
            purge_dir(pl_dir)
        if sub_target == "search":
            full_ver = PdfiumVer.to_full(pdfium_ver) if pdfium_ver else None
            full_ver = system_pdfium.main(full_ver, flags=flags)
        elif sub_target == "generate":
            assert pdfium_ver, "system-generate target requires pdfium build version from caller"
            build_pdfium_bindings(pdfium_ver, flags=flags, guard_symbols=True, rt_paths=())
            shutil.copyfile(BindingsFile, pl_dir/BindingsFN)
            full_ver = PdfiumVer.to_full(pdfium_ver)
            write_pdfium_info(pl_dir, full_ver, origin="system-generate", flags=flags)
        else:
            _end_subtargets(sub_target, pdfium_ver)
    
    elif pl_name == ExtPlats.sourcebuild:
        if flags:
            log(f"sourcebuild: flags {flags!r} are not handled (will be discarded).")
        
        if sub_target:
            builder = dict(native=build_native, toolchained=build_toolchained)[sub_target]
            build_params_env = shlex.split( os.getenv("BUILD_PARAMS", default_build_params) )
            build_params = vars(builder.parse_args(build_params_env))
            build_params.update(dict(build_ver=pdfium_ver))
            log(build_params)
            builder.main(**build_params)
        else:
            _end_subtargets(sub_target, pdfium_ver)
    
    elif pl_name == ExtPlats.fallback:
        pl_name = ExtPlats.system
        try:
            stage_platfiles(pl_name, "search", pdfium_ver, flags)
        except system_pdfium.PdfiumNotFoundError:
            log("Could not find system pdfium, will attempt native sourcebuild")
            pl_name = ExtPlats.sourcebuild
            try:
                bootstrap_buildtools()
                stage_platfiles(pl_name, "native", pdfium_ver, flags, "--vendor all --no-vendor libc++")
            except Exception:
                traceback.print_exc()
                raise RuntimeError("sourcebuild-native failed. Manual action may be needed, such as installing system dependencies, or possibly patching the sources. See pypdfium2's README.md for more information.")
    
    else:
        if not pdfium_ver or pdfium_ver == "pinned":
            pdfium_ver = PdfiumVer.pinned
            log(f"Using pinned pdfium version {pdfium_ver!r}. If this is not intentional, set e.g. {PlatSpec_EnvVar}=auto:latest to use the latest version instead.")
        elif pdfium_ver == "latest":
            pdfium_ver = PdfiumVer.get_latest()
            log(f"Using latest pdfium-binaries version {pdfium_ver!r}.")
        assert pl_name and hasattr(PlatNames, pl_name)
        _get_pdfium_with_cache(pl_name, pdfium_ver, flags)
    
    return pl_name


def copy_platfiles(pl_name):
    
    # remove existing in-tree platform files, if any
    clean_platfiles()
    
    # the version file is in the platform directory for all targets
    pl_dir = DataDir/pl_name
    platfiles = [pl_dir/VersionFN]
    
    # For system and sourcebuild, the bindings file is in the platform directory.
    # For the pdfium-binaries targets, the bindings are shared in data/bindings/
    if pl_name == ExtPlats.system:
        platfiles.append(pl_dir/BindingsFN)
    elif pl_name == ExtPlats.sourcebuild:
        platfiles.append(pl_dir/BindingsFN)
        platfiles.extend(p for p in pl_dir.glob(Host.libname_glob))
    else:
        platfiles.append(BindingsFile)
        system = plat_to_system(pl_name)
        platfiles.append(pl_dir/libname_for_system(system))
    
    assert all(fp.exists() for fp in platfiles), "Some platform files are missing"
    for fp in platfiles:
        shutil.copy(fp, ModuleDir_Raw/fp.name)
    
    return tuple(fp.name for fp in platfiles)


def prepare_setup(pl_name, sub_target, pdfium_ver, flags):
    # Write platform files into a data staging directory
    pl_name = stage_platfiles(pl_name, sub_target, pdfium_ver, flags)
    # Copy platform files into actual source tree
    platfiles = copy_platfiles(pl_name)
    return platfiles, pl_name


def main():
    
    parser = argparse.ArgumentParser(
        description = "Manage in-tree artifacts from an editable install.",
    )
    parser.add_argument(
        "plat_spec",
        default = os.environ.get(PlatSpec_EnvVar, ""),
        nargs = "?",
        help = f"The platform specifier. Same format as of ${PlatSpec_EnvVar} on setup. {ExtPlats.sdist!r} removes existing artifacts.",
    )
    args = parser.parse_args()
    
    if args.plat_spec == ExtPlats.sdist:
        log("Remove existing in-tree platform files, if any.")
        clean_platfiles()
        return
    
    pl_name, *pl_info = parse_pl_spec(args.plat_spec)
    prepare_setup(pl_name, *pl_info)


if __name__ == "__main__":
    main()
