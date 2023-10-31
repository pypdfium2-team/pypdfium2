# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import shutil
import argparse
import tempfile
from pathlib import Path
from functools import partial

sys.path.insert(0, str(Path(__file__).parents[1]))
# TODO consider dotted access?
from pypdfium2_setup.packaging_base import *
from pypdfium2_setup.emplace import prepare_setup


P_PYPI = "pypi"
P_CONDA_BUNDLE = "conda_bundle"
P_CONDA_RAW = "conda_raw"
P_CONDA_HELPERS = "conda_helpers"

CondaChannels = ("-c", "bblanchon", "-c", "pypdfium2-team")
CondaDir = ProjectDir / "conda"


def parse_args():
    
    root_parser = argparse.ArgumentParser(
        description = "Craft PyPI or conda packages for pypdfium2.",
    )
    root_parser.add_argument(
        "--pdfium-ver",
        type = int,
        default = None,
    )
    subparsers = root_parser.add_subparsers(dest="parser")
    pypi = subparsers.add_parser(P_PYPI)
    conda_raw = subparsers.add_parser(P_CONDA_RAW)
    conda_helpers = subparsers.add_parser(P_CONDA_HELPERS)
    conda_bundle = subparsers.add_parser(P_CONDA_BUNDLE)
    conda_bundle.add_argument(
        "--platforms",
        nargs = "+",
        default = [Host.platform],
    )
    conda_bundle.add_argument(
        "--py-variants",
        nargs = "*",
    )
    
    for p in (pypi, conda_bundle):
        p.add_argument(
            "--use-v8",
            action = "store_true",
        )
    
    args = root_parser.parse_args()
    if not args.pdfium_ver:
        args.pdfium_ver = PdfiumVer.get_latest()
    if args.parser == P_CONDA_BUNDLE:
        if args.platforms and args.platforms[0] == "all":
            args.platforms = list(CondaNames.keys())
        if args.py_variants and args.py_variants[0] == "all":
            args.py_variants = ["3.8", "3.9", "3.10", "3.11", "3.12"]
    
    return args


def run_pypi_build(args):
    run_cmd([sys.executable, "-m", "build", "--skip-dependency-check", "--no-isolation"] + args, cwd=ProjectDir, env=os.environ)

def main_pypi(args):
    
    os.environ[PlatSpec_EnvVar] = ExtPlats.none
    run_pypi_build(["--sdist"])
    
    suffix = build_pl_suffix(args.pdfium_ver, args.use_v8)
    for plat in ReleaseNames.keys():
        os.environ[PlatSpec_EnvVar] = plat + suffix
        run_pypi_build(["--wheel"])
        clean_platfiles()


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


def run_conda_build(recipe_dir, out_dir, args=[]):
    with TmpCommitCtx():
        run_cmd(["conda", "build", recipe_dir, "--output-folder", out_dir, *args, *CondaChannels], cwd=ProjectDir, env=os.environ)


CondaNames = {
    # NOTE looks like conda doesn't support musllinux yet ...
    PlatNames.darwin_x64     : "osx-64",
    PlatNames.darwin_arm64   : "osx-arm64",
    PlatNames.linux_x64      : "linux-64",
    PlatNames.linux_x86      : "linux-32",
    PlatNames.linux_arm64    : "linux-aarch64",
    PlatNames.linux_arm32    : "linux-armv7l",
    PlatNames.windows_x64    : "win-64",
    PlatNames.windows_x86    : "win-32",
    PlatNames.windows_arm64  : "win-arm64",
}

def _run_conda_bundle(args, pl_name, suffix, conda_args):
    
    os.environ["IN_"+PlatSpec_EnvVar] = pl_name + suffix
    emplace_func = partial(prepare_setup, pl_name, args.pdfium_ver, args.use_v8)
    
    with CondaExtPlatfiles(emplace_func):
        run_conda_build(CondaDir/"bundle", CondaDir/"bundle"/"out", conda_args)


def main_conda_bundle(args):

    helpers_ver = merge_tag(parse_git_tag(), "py")
    os.environ["VERSION"] = helpers_ver
    
    platforms = args.platforms.copy()
    with_host = Host.platform in platforms
    if with_host:
        platforms.remove(Host.platform)
    conda_host = CondaNames[Host.platform]
    host_files = None
    
    conda_args = []
    if args.py_variants:
        conda_args += ["--variants", "{python: %s}" % (args.py_variants, )]
    suffix = build_pl_suffix(args.pdfium_ver, args.use_v8)
    
    for pl_name in platforms:
        
        _run_conda_bundle(args, pl_name, suffix, [*conda_args, "--no-test"])
        if not host_files:
            host_files = list((CondaDir/"bundle"/"out"/conda_host).glob(f"pypdfium2_bundle-{helpers_ver}-*.tar.bz2"))
        
        run_cmd(["conda", "convert", "-f", *host_files, "-p", CondaNames[pl_name], "-o", CondaDir/"bundle"/"out"], cwd=ProjectDir, env=os.environ)
        for hf in host_files:
            hf.unlink()
    
    if with_host:
        _run_conda_bundle(args, Host.platform, suffix, conda_args)


def main_conda_raw(args):
    os.environ["PDFIUM_SHORT"] = str(args.pdfium_ver)
    os.environ["PDFIUM_FULL"] = PdfiumVer.to_full(args.pdfium_ver, type=str)
    emplace_func = partial(prepare_setup, ExtPlats.system, args.pdfium_ver, use_v8=None)
    with CondaExtPlatfiles(emplace_func):
        run_conda_build(CondaDir/"raw", CondaDir/"raw"/"out")


def main_conda_helpers(args):
    
    # Set the current pdfium version as upper boundary, for inherent API safety.
    # Unfortunately, pdfium does not do semantic versioning, so it is hard to achieve safe upward flexibility.
    # See also https://groups.google.com/g/pdfium/c/kCmgW_gTFYE/m/BPoJgbwOCQAJ
    # In case risk of conflicts becomes a problem, we could estimate an increase based on pdfium's deprecation period.
    # Relevant variables for such a calculation would be
    # - version increment speed (guess: average 2 per day)
    # - pdfium's lowest regular deprecation period (say: 6 months, as indicated by pdfium/CONTRIBUTING.md)
    # - a buffer zone for us to recognize a deprecation (say: 2 months)
    # Assuming a month has 30 days, this would result in
    #   2 * 30 * (6-2) = 240
    os.environ["PDFIUM_MAX"] = str(args.pdfium_ver)
    
    # NOTE To build with a local pypdfium2_raw, add the args below for the source dir, and remove the pypdfium2-team prefix from the helpers recipe's run requirements
    # args=["-c", CondaDir/"raw"/"out"]
    run_conda_build(CondaDir/"helpers", CondaDir/"helpers"/"out")


class TmpCommitCtx:
    
    # https://github.com/conda/conda-build/issues/5045
    # Work around local conda `git_url` not including uncommitted changes
    # We can't reasonably use `path` since it does not honor gitignore rules, but would copy all files, including big generated directories like sourcebuild/
    # On the other hand, transferring generated files with `git_url` tends to be problematic, as a tmp commit renders the initial repo state invalid.
    # Alternatively, we could perhaps make a clean copy of required files (e.g. using the sdist) and using `path` instead of git hacks?
    
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


def main():
    
    args = parse_args()
    
    with ArtifactStash():
        if args.parser == P_PYPI:
            main_pypi(args)
        elif args.parser.startswith("conda"):
            helpers_info = parse_git_tag()
            os.environ["M_HELPERS_VER"] = merge_tag(helpers_info, "py")
            if args.parser == P_CONDA_BUNDLE:
                main_conda_bundle(args)
            elif args.parser == P_CONDA_RAW:
                main_conda_raw(args)
            elif args.parser == P_CONDA_HELPERS:
                main_conda_helpers(args)
            else:
                assert False
        else:
            assert False


if __name__ == '__main__':
    main()
