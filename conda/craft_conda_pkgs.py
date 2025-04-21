# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import argparse
from pathlib import Path
from functools import partial

sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from pypdfium2_setup.base import *
from pypdfium2_setup.emplace import prepare_setup
from pypdfium2_setup.craft import ArtifactStash

CondaDir = ProjectDir / "conda"
CondaRaw_BuildNumF = CondaDir / "raw" / "build_num.txt"

T_RAW = "raw"
T_HELPERS = "helpers"


def main():
    parser = argparse.ArgumentParser(
        description = "Craft conda packages for pypdfium2"
    )
    parser.add_argument(
        "type",
        choices = (T_RAW, T_HELPERS),
        help = "The package type to build (raw or helpers)",
    )
    parser.add_argument("--pdfium-ver", default=None)
    parser.add_argument("--new-only", action="store_true")
    
    args = parser.parse_args()
    if args.type == T_RAW:
        with ArtifactStash():
            main_conda_raw(args)
    elif args.type == T_HELPERS:
        assert not args.new_only, "--new-only / buildnum handling not implemented for helpers package"
        main_conda_helpers(args)
    else:
        assert False  # unreached, handled by argparse


def _handle_ver(args, get_latest):
    if not args.pdfium_ver or args.pdfium_ver == "latest":
        args.pdfium_ver = get_latest()
    else:
        args.pdfium_ver = int(args.pdfium_ver)


def main_conda_raw(args):
    
    _handle_ver(args, CondaPkgVer.get_latest_pdfium)
    os.environ["PDFIUM_SHORT"] = str(args.pdfium_ver)
    os.environ["PDFIUM_FULL"] = ".".join([str(v) for v in PdfiumVer.to_full(args.pdfium_ver)])
    os.environ["BUILD_NUM"] = str(_get_build_num(args))
    
    emplace_func = partial(prepare_setup, ExtPlats.system, args.pdfium_ver, use_v8=None)
    with CondaExtPlatfiles(emplace_func):
        run_conda_build(CondaDir/"raw", CondaDir/"raw"/"out", args=["--override-channels", "-c", "bblanchon", "-c", "defaults"])


def main_conda_helpers(args):
    
    _handle_ver(args, CondaPkgVer.get_latest_bindings)
    helpers_info = parse_git_tag()
    os.environ["M_HELPERS_VER"] = merge_tag(helpers_info, "py")
    
    # Pass the minimum pdfium requirement by env variable.
    # This is so we can share the value and need to change it only in one place.
    os.environ["PDFIUM_MIN"] = PDFIUM_MIN_REQ
    # Set the current pdfium version as upper boundary, for inherent API safety.
    # pdfium does not do semantic versioning, so upward flexibility is difficult.
    os.environ["PDFIUM_MAX"] = str(args.pdfium_ver)
    
    # NOTE To build with a local pypdfium2_raw, add the args below for the source dir, and remove the pypdfium2-team prefix from the helpers recipe's run requirements
    # args=["-c", CondaDir/"raw"/"out"]
    run_conda_build(CondaDir/"helpers", CondaDir/"helpers"/"out", args=["--override-channels", "-c", "pypdfium2-team", "-c", "bblanchon", "-c", "defaults"])


def run_conda_build(recipe_dir, out_dir, args=()):
    with TmpCommitCtx():
        run_cmd(["conda", "build", recipe_dir, "--output-folder", out_dir, *args], cwd=ProjectDir, env=os.environ)


@functools.lru_cache(maxsize=2)
def run_conda_search(package, channel):
    output = run_cmd(["conda", "search", "--json", package, "--override-channels", "-c", channel], cwd=None, capture=True)
    return json.loads(output)[package]


class CondaPkgVer:

    @staticmethod
    @functools.lru_cache(maxsize=2)
    def _get_latest_for(package, channel, v_func):
        search = run_conda_search(package, channel)
        search = sorted(search, key=lambda d: v_func(d["version"]), reverse=True)
        result = v_func(search[0]["version"])
        print(f"Resolved latest {channel}::{package} to {result}", file=sys.stderr)
        return result
    
    @staticmethod
    def get_latest_pdfium():
        return CondaPkgVer._get_latest_for(
            "pdfium-binaries", "bblanchon", lambda v: int(v.split(".")[2])
        )
    
    @staticmethod
    def get_latest_bindings():
        return CondaPkgVer._get_latest_for(
            "pypdfium2_raw", "pypdfium2-team", lambda v: int(v)
        )


def _get_build_num(args):
    
    # parse existing releases to automatically handle arbitrary version builds
    # TODO expand to pypdfium2_helpers as well, so we could rebuild with different pdfium bounds in a workflow
    
    search = reversed(run_conda_search("pypdfium2_raw", "pypdfium2-team"))
    
    if args.new_only:
        # or `args.pdfium_ver not in {...}` to allow new builds of older versions
        assert args.pdfium_ver > max(int(d["version"]) for d in search), f"--new-only given, but {args.pdfium_ver} already has a build"
    
    # determine build number
    build_num = max((d["build_number"] for d in search if int(d["version"]) == args.pdfium_ver), default=None)
    build_num = 0 if build_num is None else build_num+1
    
    return build_num


class TmpCommitCtx:
    
    # Work around local conda `git_url` not including uncommitted changes
    # In particular, this is used to transfer data files, so we can generate them externally and don't have to conda package ctypesgen.
    
    # use a tmp control file so we can also undo the commit in conda's isolated clone
    FILE = CondaDir / "with_tmp_commit.txt"
    
    def __enter__(self):
        # determine if there are any modified or new files
        out = run_cmd(["git", "status", "--porcelain"], capture=True, cwd=ProjectDir)
        self.have_mods = bool(out)
        if self.have_mods:  # make tmp commit
            self.FILE.touch()
            run_cmd(["git", "add", "."], cwd=ProjectDir)
            run_cmd(["git", "commit", "-m", "!!! tmp commit for conda-build", "-m", "make conda-build include uncommitted changes"], cwd=ProjectDir)
    
    @classmethod
    def undo(cls):
        # assuming FILE exists (promised by callers)
        run_cmd(["git", "reset", "--soft", "HEAD^"], cwd=ProjectDir)
        run_cmd(["git", "reset", cls.FILE], cwd=ProjectDir)
        cls.FILE.unlink()
    
    def __exit__(self, *_):
        if self.have_mods:  # pop tmp commit, if any
            self.undo()


class CondaExtPlatfiles:
    
    def __init__(self, emplace_func):
        self.emplace_func = emplace_func
    
    def __enter__(self):
        self.platfiles = self.emplace_func()
        self.platfiles = [ModuleDir_Raw/f for f in self.platfiles]
        run_cmd(["git", "add", "-f"] + [str(f) for f in self.platfiles], cwd=ProjectDir)
    
    def __exit__(self, *_):
        run_cmd(["git", "reset"] + [str(f) for f in self.platfiles], cwd=ProjectDir)
        for fp in self.platfiles:
            fp.unlink()


if __name__ == "__main__":
    main()
