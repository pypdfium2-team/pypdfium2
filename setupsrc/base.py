# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import re
import shutil
import tarfile
import contextlib
from pathlib import Path
import urllib.request as url_request

# local
from _corebase import *
from _version import *


@contextlib.contextmanager
def tmp_cwd_context(tmp_cwd):
    orig_cwd = os.getcwd()
    os.chdir(str(tmp_cwd.resolve()))
    try:
        yield
    finally:
        os.chdir(orig_cwd)


CTG_LIBPATTERN = "{prefix}{name}.{suffix}"

# TODO make version mandatory
def run_ctypesgen(
        target_path, headers_dir, flags=(),
        rt_paths=(f"./{CTG_LIBPATTERN}", ), ct_paths=(), univ_paths=(),
        search_sys_despite_libpaths=False,
        guard_symbols=False, no_srcinfo=False, version=None
    ):
    
    if USE_REFBINDINGS:
        log("Using reference bindings - this will bypass all bindings params. If this is not intentional, make sure ctypesgen is installed.")
        record_ver = PdfiumVer.pinned
        if version != record_ver:
            log(f"Warning: binary/bindings version mismatch ({version} != {record_ver}). This is ABI-unsafe!")
        shutil.copyfile(RefBindingsFile, target_path)
        return target_path
    
    # Import ctypesgen only in this function so it does not have to be available for other setup tasks
    import ctypesgen
    assert getattr(ctypesgen, "PYPDFIUM2_SPECIFIC", False), "pypdfium2 requires fork of ctypesgen"
    import ctypesgen.__main__
    
    # library loading
    args = ["-l", "pdfium"]
    if rt_paths:
        args += ["--rt-libpaths", *rt_paths]
    if univ_paths:
        args += ["--univ-libpaths", *univ_paths]
    if (rt_paths or univ_paths) and not search_sys_despite_libpaths:
        args += ["--no-system-libsearch"]
    if ct_paths:
        args += ["--ct-libpaths", *ct_paths]
    else:
        args += ["--no-load-library"]
    
    # style
    args += ["--no-macro-guards"]
    if not guard_symbols:
        args += ["--no-symbol-guards"]
    if no_srcinfo:
        args += ["--no-srcinfo"]
    
    # pre-processor - if not given, pypdfium2-ctypesgen will try to auto-select as available (gcc/clang)
    c_preproc = os.environ.get("CPP", None)
    if c_preproc:
        args += ["--cpp", c_preproc]
    if flags:
        args += ["-D"] + [PdfiumFlagsDict[f] for f in flags]
    if Host.system == SysNames.windows:
        # If we are on a Windows host, add the relevant define to expose Windows-only members.
        # Note, this is not currently active for our wheels, since we're packaging everything on Linux. It might be possible to divide packaging in native OS hosts in the future, or specify external headers for symbol spoofing.
        args += ["-D", "_WIN32"]
    
    # symbols - try to exclude some garbage aliases that get pulled in from struct tags
    # (this captures anything that ends with _, _t, or begins with _, and is not needed by other symbols)
    args += ["--symbol-rules", r"if_needed=\w+_$|\w+_t$|_\w+"]
    
    # input / output
    args += ["--headers"] + [h.name for h in sorted(headers_dir.glob("*.h"))] + ["-o", target_path]
    
    with tmp_cwd_context(headers_dir):
        ctypesgen.__main__.main([str(a) for a in args])


def _make_json_compat(obj):
    if isinstance(obj, dict):
        return {k: _make_json_compat(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_json_compat(v) for v in obj]
    elif isinstance(obj, Path):
        return str(obj)
    else:
        return obj


def tar_extract_file(tar, path_or_member, dst_path):
    src_buf = tar.extractfile(path_or_member)
    assert src_buf is not None, f"Failed to extract {path_or_member}"
    with open(dst_path, "wb") as dst_buf:
        shutil.copyfileobj(src_buf, dst_buf)


def build_pdfium_bindings(version, headers_dir=None, **kwargs):
    
    ver_path = DataDir_Bindings/VersionFN
    bind_path = BindingsFile
    if not headers_dir:
        headers_dir = DataDir_Bindings/"headers"
    
    # TODO register all defaults?
    curr_info = {"version": version, **kwargs}
    curr_info.pop("ct_paths", None)  # ignore
    curr_info.setdefault("flags", [])
    curr_info = _make_json_compat(curr_info)
    
    prev_ver = None
    if ver_path.exists():
        prev_info = read_json(ver_path)
        prev_ver = prev_info["version"]
        if bind_path.exists() and prev_info == curr_info:
            log(f"Using cached bindings")
            return
        else:
            log(f"Bindings cache state differs:", prev_info, curr_info, sep="\n")
    
    # try to reuse headers if only bindings params differ, not version
    if prev_ver == version and headers_dir.exists() and list(headers_dir.glob("fpdf*.h")):
        log("Using cached headers")
    else:
        log("Downloading headers...")
        mkdir(headers_dir)
        archive_url = f"{PdfiumURL}/+archive/refs/heads/chromium/{version}/public.tar.gz"
        archive_path = DataDir_Bindings / "pdfium_public.tar.gz"
        url_request.urlretrieve(archive_url, archive_path)
        with tarfile.open(archive_path) as tar:
            for m in tar.getmembers():
                if m.isfile() and re.fullmatch(r"fpdf(\w+)\.h", m.name, flags=re.ASCII):
                    tar_extract_file(tar, m, headers_dir/m.name)
        archive_path.unlink()
    
    log(f"Building bindings ...")
    bindings_path = DataDir_Bindings/BindingsFN
    run_ctypesgen(bindings_path, headers_dir, version=version, **kwargs)
    write_json(ver_path, curr_info)


def clean_platfiles():
    
    deletables = [
        ProjectDir / "build",
        ModuleDir_Raw / BindingsFN,
        ModuleDir_Raw / VersionFN,
    ]
    for pattern in LIBNAME_GLOBS:
        deletables += ModuleDir_Raw.glob(pattern)
    
    for fp in deletables:
        if fp.is_file():
            fp.unlink()
        elif fp.is_dir():
            shutil.rmtree(fp)


def build_pl_suffix(version, use_v8):
    return (PlatSpec_V8Sym if use_v8 else "") + PlatSpec_VerSep + str(version)


def parse_pl_spec(pl_spec):
    
    # TODO split up in individual env vars after all?
    
    req_ver, flags = None, ()
    if PlatSpec_VerSep in pl_spec:
        pl_spec, req_ver = pl_spec.rsplit(PlatSpec_VerSep)
    if pl_spec.endswith(PlatSpec_V8Sym):
        pl_spec, flags = pl_spec[:-len(PlatSpec_V8Sym)], ("V8", "XFA")
    
    subspec = None
    if not pl_spec or pl_spec == "auto":
        if Host.platform is None:
            log(str(Host._exc))
            pl_name = ExtPlats.fallback
        else:
            pl_name = Host.platform
    else:
        if "-" in pl_spec:
            pl_spec, subspec = pl_spec.split("-", maxsplit=1)
        if hasattr(ExtPlats, pl_spec):
            pl_name = getattr(ExtPlats, pl_spec)
        elif hasattr(PlatNames, pl_spec):
            pl_name = getattr(PlatNames, pl_spec)
        else:
            raise ValueError(f"Invalid binary spec '{pl_spec}'")
    
    if req_ver and req_ver.isnumeric():
        req_ver = int(req_ver)
    
    return pl_name, subspec, req_ver, flags


def parse_modspec(modspec):
    if modspec:
        modnames = modspec.split(",")
        assert set(modnames).issubset(ModulesAll)
        assert len(modnames) in (1, 2)
    else:
        modnames = ModulesAll
    return modnames


def get_next_changelog(flush=False):
    
    content = ChangelogStaging.read_text()
    pos = content.index("\n", content.index("# Changelog")) + 1
    header = content[:pos].strip() + "\n"
    devel_msg = content[pos:].strip()
    if devel_msg:
        devel_msg += "\n"
    
    if flush:
        ChangelogStaging.write_text(header)
    
    return devel_msg


def purge_dir(dir):
    if dir.exists():
        shutil.rmtree(dir)
    dir.mkdir(parents=True)
