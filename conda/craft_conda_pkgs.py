# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from base import *
from craft import ArtifactStash
from emplace import stage_platfiles

CondaDir = ProjectDir / "conda"
CondaRaw_BuildNumF = CondaDir / "raw" / "build_num.txt"

T_RAW = "raw"
T_HELPERS = "helpers"


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


def run_conda_build(recipe_dir, out_dir, args=()):
    with TmpCommitCtx():
        run_cmd(["conda", "build", recipe_dir, "--output-folder", out_dir, *args], cwd=ProjectDir, env=os.environ)


def _handle_ver(args, get_latest):
    if not args.pdfium_ver or args.pdfium_ver == "latest":
        args.pdfium_ver = get_latest()
    else:
        args.pdfium_ver = int(args.pdfium_ver)


def _get_build_num(package, planned_ver, new_only):
    # infer build number from existing releases to automatically handle arbitrary version builds
    search = reversed(run_conda_search(package, "pypdfium2-team"))
    build_num = max((d["build_number"] for d in search if d["version"] == planned_ver), default=None)
    build_num = 0 if build_num is None else build_num+1
    if new_only and build_num > 0:
        raise RuntimeError(f"--new-only given, but {planned_ver} already has a build")
    log(f"Determined build number {build_num}")
    return build_num


class CondaExtPlatfiles:
    
    def __enter__(self):
        sys_dir = DataDir/ExtPlats.system
        self.platfiles = [sys_dir/BindingsFN, sys_dir/VersionFN, ModuleDir_Raw/VersionFN]
        shutil.copyfile(sys_dir/VersionFN, ModuleDir_Raw/VersionFN)
        run_cmd(["git", "add", "-f"] + [str(f) for f in self.platfiles], cwd=ProjectDir)
    
    def __exit__(self, *_):
        run_cmd(["git", "reset"] + [str(f) for f in self.platfiles], cwd=ProjectDir)
        for fp in self.platfiles:
            fp.unlink()


def main_conda_raw(args):
    
    _handle_ver(args, CondaPkgVer.get_latest_pdfium)
    os.environ["PDFIUM_SHORT"] = str(args.pdfium_ver)
    assert not (IGNORE_FULLVER or GIVEN_FULLVER)
    full_ver = PdfiumVer.to_full(args.pdfium_ver)
    os.environ["PDFIUM_FULL"] = str(full_ver)
    build_num = _get_build_num("pypdfium2_raw", str(args.pdfium_ver), args.new_only)
    os.environ["BUILD_NUM"] = str(build_num)
    
    stage_platfiles(ExtPlats.system, "generate", args.pdfium_ver, flags=())
    with CondaExtPlatfiles():
        run_conda_build(CondaDir/"raw", CondaDir/"raw"/"out", args=["--override-channels", "-c", "bblanchon", "-c", "defaults"])


def main_conda_helpers(args):
    
    _handle_ver(args, CondaPkgVer.get_latest_bindings)
    helpers_info = parse_git_tag()
    helpers_ver = merge_tag(helpers_info, mode=None)  # XXX
    os.environ["M_HELPERS_VER"] = helpers_ver
    
    build_num = _get_build_num("pypdfium2_helpers", helpers_ver, args.new_only)
    os.environ["BUILD_NUM"] = str(build_num)
    
    # Pass the minimum pdfium requirement by env variable.
    # This is so we can share the value and need to change it only in one place.
    os.environ["PDFIUM_MIN"] = str(PDFIUM_MIN_REQ)
    # Set the current pdfium version as upper boundary, for inherent API safety.
    # Upward flexibility is difficult. For one thing, pdfium does not do semantic versioning. For another, unforeseen issues can crop up anytime, and we do not want them to break older releases.
    os.environ["PDFIUM_MAX"] = str(args.pdfium_ver)
    
    # NOTE To build with a local pypdfium2_raw, add the args below for the source dir, and remove the pypdfium2-team prefix from the helpers recipe's run requirements
    # args=["-c", CondaDir/"raw"/"out"]
    run_conda_build(CondaDir/"helpers", CondaDir/"helpers"/"out", args=["--override-channels", "-c", "pypdfium2-team", "-c", "bblanchon", "-c", "defaults"])


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
        main_conda_helpers(args)
    else:
        assert False  # unreached, handled by argparse


if __name__ == "__main__":
    main()
