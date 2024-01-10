# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# TODO split in pypi and conda?

import os
import sys
import json
import shutil
import argparse
import tempfile
import contextlib
import urllib.request as url_request
from pathlib import Path
from functools import partial

sys.path.insert(0, str(Path(__file__).parents[1]))
# TODO consider dotted access?
from pypdfium2_setup.packaging_base import *
from pypdfium2_setup.emplace import prepare_setup


P_PYPI = "pypi"
P_CONDA_RAW = "conda_raw"
P_CONDA_HELPERS = "conda_helpers"

def parse_args():
    
    root_parser = argparse.ArgumentParser(
        description = "Craft PyPI or conda packages for pypdfium2.",
    )
    root_parser.add_argument(
        "--pdfium-ver",
        default = None,
    )
    subparsers = root_parser.add_subparsers(dest="parser")
    pypi = subparsers.add_parser(P_PYPI)
    pypi.add_argument(
        "--use-v8",
        action = "store_true",
    )
    conda_raw = subparsers.add_parser(P_CONDA_RAW)
    conda_helpers = subparsers.add_parser(P_CONDA_HELPERS)
    
    args = root_parser.parse_args()
    args.is_literal_latest = args.pdfium_ver == "latest"
    if not args.pdfium_ver or args.is_literal_latest:
        if args.parser == P_CONDA_RAW:
            args.pdfium_ver = PdfiumVer.get_latest_conda_pdfium()
        elif args.parser == P_CONDA_HELPERS:
            args.pdfium_ver = PdfiumVer.get_latest_conda_bindings()
        else:
            args.pdfium_ver = PdfiumVer.get_latest()
    else:
        args.pdfium_ver = int(args.pdfium_ver)
    
    return args


def main():
    
    args = parse_args()
    
    with ArtifactStash():
        if args.parser == P_PYPI:
            main_pypi(args)
        elif args.parser == P_CONDA_RAW:
            main_conda_raw(args)
        elif args.parser == P_CONDA_HELPERS:
            helpers_info = parse_git_tag()
            os.environ["M_HELPERS_VER"] = merge_tag(helpers_info, "py")
            main_conda_helpers(args)
        else:
            assert False


def _run_pypi_build(args):
    # -nx: --no-isolation --skip-dependency-check
    run_cmd([sys.executable, "-m", "build", "-nx"] + args, cwd=ProjectDir, env=os.environ)


def main_pypi(args):
    
    os.environ[PlatSpec_EnvVar] = ExtPlats.sdist
    with tmp_ctypesgen_pin():
        _run_pypi_build(["--sdist"])
    
    suffix = build_pl_suffix(args.pdfium_ver, args.use_v8)
    for plat in ReleaseNames.keys():
        os.environ[PlatSpec_EnvVar] = plat + suffix
        _run_pypi_build(["--wheel"])
        clean_platfiles()


def run_conda_build(recipe_dir, out_dir, args=[]):
    with TmpCommitCtx():
        run_cmd(["conda", "build", recipe_dir, "--output-folder", out_dir, *args], cwd=ProjectDir, env=os.environ)


def _get_build_num(args):
    
    # parse existing releases to automatically handle arbitrary version builds
    # TODO expand to pypdfium2_helpers as well, so we could rebuild with different pdfium bounds in a workflow
    
    search = reversed(run_conda_search("pypdfium2_raw", "pypdfium2-team"))
    
    if args.is_literal_latest:
        assert args.pdfium_ver > max([int(d["version"]) for d in search]), "Literal latest must resolve to a new version. This is done to avoid rebuilds without new version in scheduled releases. If you want to rebuild, omit --pdfium-ver or pass the resolved value."
    
    # determine build number
    build_num = max([d["build_number"] for d in search if int(d["version"]) == args.pdfium_ver], default=None)
    build_num = 0 if build_num is None else build_num+1
    
    return build_num


def main_conda_raw(args):
    os.environ["PDFIUM_SHORT"] = str(args.pdfium_ver)
    os.environ["PDFIUM_FULL"] = ".".join([str(v) for v in PdfiumVer.to_full(args.pdfium_ver)])
    os.environ["BUILD_NUM"] = str(_get_build_num(args))
    emplace_func = partial(prepare_setup, ExtPlats.system, args.pdfium_ver, use_v8=None)
    with CondaExtPlatfiles(emplace_func):
        run_conda_build(CondaDir/"raw", CondaDir/"raw"/"out", args=["--override-channels", "-c", "bblanchon"])


def main_conda_helpers(args):
    
    # Set the current pdfium version as upper boundary, for inherent API safety.
    # pdfium does not do semantic versioning, so upward flexibility is difficult.
    os.environ["PDFIUM_MAX"] = str(args.pdfium_ver)
    
    # NOTE To build with a local pypdfium2_raw, add the args below for the source dir, and remove the pypdfium2-team prefix from the helpers recipe's run requirements
    # args=["-c", CondaDir/"raw"/"out"]
    run_conda_build(CondaDir/"helpers", CondaDir/"helpers"/"out", args=["--override-channels", "-c", "pypdfium2-team", "-c", "bblanchon"])


class ArtifactStash:
    
    # Preserve in-tree aftefacts from editable install
    
    def __enter__(self):
        
        self.tmpdir = None
        
        file_names = [VersionFN, BindingsFN, LibnameForSystem[Host.system]]
        self.files = [fp for fp in [ModuleDir_Raw / fn for fn in file_names] if fp.exists()]
        if len(self.files) == 0:
            return
        
        self.tmpdir = tempfile.TemporaryDirectory(prefix="pypdfium2_artifact_stash_")
        self.tmpdir_path = Path(self.tmpdir.name)
        for fp in self.files:
            shutil.move(fp, self.tmpdir_path)
    
    def __exit__(self, *_):
        if self.tmpdir is None:
            return
        for fp in self.files:
            shutil.move(self.tmpdir_path / fp.name, ModuleDir_Raw)
        self.tmpdir.cleanup()


@contextlib.contextmanager
def tmp_replace_ctx(fp, orig, tmp):
    orig_txt = fp.read_text()
    tmp_txt = orig_txt.replace(orig, tmp)
    fp.write_text(tmp_txt)
    try:
        yield
    finally:
        fp.write_text(orig_txt)


@contextlib.contextmanager
def tmp_ctypesgen_pin():
    
    head_url = "https://api.github.com/repos/pypdfium2-team/ctypesgen/git/refs/heads/pypdfium2"
    with url_request.urlopen(head_url) as rq:
        content = rq.read().decode()
    content = json.loads(content)
    sha = content["object"]["sha"]
    print(f"Resolved pypdfium2 ctypesgen HEAD to {sha}", file=sys.stderr)
    
    base_txt = "ctypesgen @ git+https://github.com/pypdfium2-team/ctypesgen@"
    ctx = tmp_replace_ctx(ProjectDir/"pyproject.toml", base_txt+"pypdfium2", base_txt+sha)
    with ctx:
        print(f"Wrote temporary pyproject.toml with ctypesgen pin", file=sys.stderr)
        yield
    print(f"Reset pyproject.toml", file=sys.stderr)


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


if __name__ == '__main__':
    main()
