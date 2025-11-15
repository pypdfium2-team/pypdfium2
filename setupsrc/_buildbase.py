# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import stat
import shutil

from base import *  # local

# The PDFium versions our build scripts have last been tested with. Ideally, they should be close to the release version in autorelease/record.json
# To bump these versions, first test locally and update any patches as needed. Then, make a branch and run "Test Sourcebuild" on CI to see if all targets continue to work. Commit the new version to the main branch only when all is green. Better stay on an older version for a while than break a target.
# Updating and testing the patch sets can be a lot of work, so we might not want to do this too frequrently.
SBUILD_NATIVE_PIN = 7191
SBUILD_TOOLCHAINED_PIN = 7191


def git_apply_patch(patch, cwd, git_args=()):
    run_cmd(["git", *git_args, "apply", "--ignore-space-change", "--ignore-whitespace", "-v", patch], cwd=cwd, check=True)


def git_clone_rev(url, rev, target_dir, depth=1):
    # https://stackoverflow.com/questions/31278902/how-to-shallow-clone-a-specific-commit-with-depth-1
    mkdir(target_dir)
    depth_param = ["--depth", str(depth)] if depth else []
    run_cmd(["git", "-c", "advice.defaultBranchName=false", "init"], cwd=target_dir)
    run_cmd(["git", "remote", "add", "origin", url], cwd=target_dir)
    run_cmd(["git", "fetch", *depth_param, "origin", rev], cwd=target_dir)
    run_cmd(["git", "-c", "advice.detachedHead=false", "checkout", "FETCH_HEAD"], cwd=target_dir)


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


_SHIMHEADERS_URL = "https://raw.githubusercontent.com/chromium/chromium/{rev}/tools/generate_shim_headers/generate_shim_headers.py"

def get_shimheaders_tool(pdfium_dir, rev="main"):

    tools_dir = pdfium_dir / "tools" / "generate_shim_headers"
    shimheaders_file = tools_dir / "generate_shim_headers.py"
    shimheaders_url = _SHIMHEADERS_URL.format(rev=rev)

    if not shimheaders_file.exists():
        log(f"Downloading {shimheaders_file.name} at revision {rev}")
        mkdir(tools_dir)
        url_request.urlretrieve(shimheaders_url, shimheaders_file)


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


def _git_get_hash(repo_dir, n_digits=None):
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
            post_ver = dict(n_commits=NaN, hash=_git_get_hash(pdfium_dir, n_digits=11))
        else:
            post_ver = dict(n_commits=0, hash=None)
    
    dest_dir = DataDir/ExtPlats.sourcebuild
    purge_dir(dest_dir)
    
    libname = libname_for_system(Host.system)
    shutil.copy(build_dir/libname, dest_dir/libname)
    
    # We want to use local headers instead of downloading with build_pdfium_bindings(), therefore call run_ctypesgen() directly
    ct_paths = (dest_dir/CTG_LIBPATTERN, ) if load_lib else ()
    run_ctypesgen(dest_dir/BindingsFN, headers_dir=pdfium_dir/"public", ct_paths=ct_paths, version=full_ver.build)
    write_pdfium_info(dest_dir, full_ver, origin=f"sourcebuild-{sub_target}", **post_ver)
    
    return full_ver, post_ver


def _make_executable(path):
    if sys.platform.startswith("win32"):
        return
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def bootstrap_ninja(skip_if_present=True):
    if skip_if_present and shutil.which("ninja"):
        return
    # https://github.com/scikit-build/ninja-python-distributions
    run_cmd([sys.executable, "-m", "pip", "install", "ninja"], cwd=None)

def bootstrap_gn(target_dir=None, skip_if_present=True):
    if skip_if_present and shutil.which("gn"):
        return
    
    if target_dir is None:
        target_dir = Host.local_bin
    
    gn_dir = ProjectDir/"sbuild"/"gn"
    url = "https://gn.googlesource.com/gn/"
    rev = "a0c5124a50608595a9aadebc4297e854ebd32c53"
    if not gn_dir.exists():
        git_clone_rev(url, rev, gn_dir, depth=1)
        git_apply_patch(PatchDir/"gn_build.patch", cwd=gn_dir)
    
    os.environ["CXX"] = "g++"
    run_cmd(["python3", "build/gen.py", "--no-last-commit-position", "--no-static-libstdc++", "--allow-warnings"], cwd=gn_dir)
    run_cmd(["ninja", "-C", "out", "gn"], cwd=gn_dir)
    del os.environ["CXX"]
    
    shutil.copyfile(gn_dir/"out"/"gn", target_dir/"gn")
    _make_executable(target_dir/"gn")

def bootstrap_buildtools():
    bootstrap_ninja()
    bootstrap_gn()
