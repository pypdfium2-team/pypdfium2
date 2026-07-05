# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import re
import shutil
from base import *  # local


def _install_dep(exename, reqfile=None):  # pkgname=None
    
    if reqfile:
        install_args = ("-r", str(reqfile))
    else:
        install_args = (exename, )  # (pkgname or exename, )
    
    which_exe = shutil.which(exename)
    if which_exe:
        log(f"+ {exename} found at {which_exe}")
        return
    
    log(f"- {exename} not found, installing...")
    run_cmd([sys.executable, "-m", "pip", "install", *install_args], cwd=None)

def install_buildtools():
    log("Check build tool dependencies...")
    # https://github.com/scikit-build/ninja-python-distributions
    _install_dep("ninja")
    # https://github.com/pypdfium2-team/gn-dist/
    _install_dep("gn", reqfile=ProjectDir/"req"/"gn.txt")

def get_clang_version(clang_root):
    from packaging.version import Version
    output = run_cmd([str(clang_root/"bin"/"clang"), "--version"], capture=True, cwd=None)
    log(output)
    version = re.search(r"version ([\d\.]+)", output).group(1)
    version = Version(version).major
    log(f"Determined clang version {version!r}")
    return version


def git_apply_patch(patch, cwd, git_args=()):
    run_cmd(["git", *git_args, "apply", "--ignore-space-change", "--ignore-whitespace", "-v", patch], cwd=cwd, check=True)

def autopatch(file, pattern, repl, is_regex, exp_count=None):
    log(f"Patch {pattern!r} -> {repl!r} (is_regex={is_regex}) on {file}")
    content = file.read_text()
    if is_regex:
        content, n_subs = re.subn(pattern, repl, content)
    else:
        n_subs = content.count(pattern)
        content = content.replace(pattern, repl)
    if exp_count is not None:
        assert n_subs == exp_count
    file.write_text(content)
    return n_subs

def autopatch_dir(dir, globexpr, pattern, repl, is_regex, exp_count=None):
    for file in dir.glob(globexpr):
        autopatch(file, pattern, repl, is_regex, exp_count)

def shared_autopatches(pdfium_dir):
    autopatch_dir(
        pdfium_dir/"public"/"cpp", "*.h",
        r'"public/(.+)"', r'"../\1"',
        is_regex=True, exp_count=None,
    )
    # bundle dependencies (e.g. abseil) into the pdfium DLL
    autopatch(
        pdfium_dir/"BUILD.gn",
        'component("pdfium")',
        'shared_library("pdfium")',
        is_regex=False, exp_count=1,
    )
    autopatch(
        pdfium_dir/"public"/"fpdfview.h",
        "#if defined(COMPONENT_BUILD)",
        "#if 1  // defined(COMPONENT_BUILD)",
        is_regex=False, exp_count=1,
    )


def _to_gn(value):
    if isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, list):
        return f"[{','.join(_to_gn(v) for v in value)}]"
    else:
        raise TypeError(f"Not sure how to serialize type {type(value).__name__}")

def serialize_gn_config(config_dict):
    parts = []
    for key, value in config_dict.items():
        parts.append(f"{key} = {_to_gn(value)}")
    result = "\n".join(parts)
    log(f"\nBuild config:\n{result}\n")
    return result


def handle_sbuild_vers(short_ver):
    if short_ver == "main":
        full_ver = PdfiumVer.get_latest_upstream()
        pdfium_rev = short_ver
        chromium_rev = short_ver
    else:
        assert str(short_ver).isnumeric()
        full_ver = PdfiumVer.to_full(short_ver)
        full_ver_str = str(full_ver)
        pdfium_rev = f"chromium/{short_ver}"
        chromium_rev = full_ver_str
    return full_ver, pdfium_rev, chromium_rev


def git_get_hash(repo_dir, n_digits=None):
    short = f"--short={n_digits}" if n_digits else "--short"
    return "g" + run_cmd(["git", "rev-parse", short, "HEAD"], cwd=repo_dir, capture=True)


def pack_sourcebuild(
        pdfium_dir, build_dir, sub_target,
        full_ver, build_ver=None, post_ver=None,
        load_lib=True,
    ):
    log("Packing data files for sourcebuild...")
    
    if not post_ver:
        assert build_ver
        if build_ver == "main":
            log("Warning: Don't know how to get number of commits with shallow checkout. A NaN placeholder will be set.")
            post_ver = dict(n_commits=NaN, hash=git_get_hash(pdfium_dir, n_digits=11))
        else:
            post_ver = dict(n_commits=0, hash=None)
    
    dest_dir = DataDir/ExtPlats.sourcebuild
    mkdir_clean(dest_dir)
    
    libname = libname_for_system(Host.system)
    shutil.copy(build_dir/libname, dest_dir/libname)
    
    # We want to use local headers instead of downloading with build_pdfium_bindings(), therefore call run_ctypesgen() directly
    ct_paths = (dest_dir/CTG_LIBPATTERN, ) if load_lib else ()
    run_ctypesgen(dest_dir/BindingsFN, headers_dir=pdfium_dir/"public", ct_paths=ct_paths, version=full_ver.build)
    write_pdfium_info(dest_dir, full_ver, origin=f"sourcebuild-{sub_target}", **post_ver)
    
    return full_ver, post_ver
