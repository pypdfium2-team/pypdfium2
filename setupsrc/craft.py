# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import json
import shutil
import argparse
import tempfile
import contextlib
import urllib.request as url_request
from pathlib import Path

from base import *  # local

try:
    import build.__main__ as build_module
except ImportError:
    build_module = None


class ArtifactStash:
    "Preserve in-tree artifacts from editable install"
    
    def __enter__(self):
        
        self.files = tuple(filter(Path.exists, (
            ModuleDir_Raw/VersionFN,
            ModuleDir_Raw/BindingsFN,
            *ModuleDir_Raw.glob(Host.libname_glob)
        )))
        if not self.files:
            return
        
        log(
            f"Stashing artifacts from editable install:\n"
            f"{tuple(fp.name for fp in self.files)}"
        )
        self.tmpdir = tempfile.TemporaryDirectory(prefix="pypdfium2_artifact_stash_")
        self.tmpdir_path = Path(self.tmpdir.name)
        for fp in self.files:
            shutil.move(fp, self.tmpdir_path)
    
    def __exit__(self, *_):
        if not self.files:
            return
        log("Restoring artifacts from editable install.")
        for fp in self.files:
            shutil.move(self.tmpdir_path/fp.name, ModuleDir_Raw)
        self.tmpdir.cleanup()


@contextlib.contextmanager
def tmp_replace_ctx(fp, orig, tmp):
    orig_txt = fp.read_text()
    assert orig_txt.count(orig) == 1
    tmp_txt = orig_txt.replace(orig, tmp)
    fp.write_text(tmp_txt)
    try:
        yield
    finally:
        fp.write_text(orig_txt)


@contextlib.contextmanager
def tmp_ctypesgen_pin():
    
    pin = os.environ.get("CTYPESGEN_PIN", None)
    if not pin:
        head_url = "https://api.github.com/repos/pypdfium2-team/ctypesgen/git/refs/heads/pypdfium2"
        with url_request.urlopen(head_url) as rq:
            content = rq.read().decode()
        content = json.loads(content)
        pin = content["object"]["sha"]
        log(f"Resolved pypdfium2 ctypesgen HEAD to SHA {pin}")
    
    base_txt = "ctypesgen @ git+https://github.com/pypdfium2-team/ctypesgen@"
    ctx = tmp_replace_ctx(ProjectDir/"pyproject.toml", base_txt+"pypdfium2", base_txt+pin)
    with ctx:
        log(f"Wrote temporary pyproject.toml with ctypesgen pin")
        yield
    log(f"Reset pyproject.toml")


def _run_pypi_build(caller_args):
    # -nx: --no-isolation --skip-dependency-check
    assert build_module, "Module 'build' is not importable. Cannot craft PyPI packages."
    with tmp_cwd_context(ProjectDir):
        build_module.main([str(ProjectDir), "-nx", *caller_args])


def main_pypi(args):
    
    assert args.sdist or args.wheels
    
    if args.sdist:
        os.environ[PlatSpec_EnvVar] = ExtPlats.sdist
        helpers_info = get_helpers_info()
        with tmp_ctypesgen_pin():
            if not helpers_info["dirty"]:
                os.environ["SDIST_IGNORE_DIRTY"] = "1"
            _run_pypi_build(["--sdist"])
    
    if args.wheels:
        suffix = build_pl_suffix(args.pdfium_ver, args.use_v8)
        for plat in WheelPlatforms:
            os.environ[PlatSpec_EnvVar] = plat + suffix
            _run_pypi_build(["--wheel"])
            clean_platfiles()


def main():
    
    parser = argparse.ArgumentParser(
        description = "Craft PyPI packages for pypdfium2"
    )
    parser.add_argument("--pdfium-ver", default=None)
    parser.add_argument("--use-v8", action="store_true")
    parser.add_argument("--wheels", action="store_true")
    parser.add_argument("--sdist", action="store_true")
    
    args = parser.parse_args()
    if not (args.wheels or args.sdist):
        args.wheels, args.sdist = True, True
    if not args.pdfium_ver or args.pdfium_ver == "latest":
        args.pdfium_ver = PdfiumVer.get_latest()
    else:
        args.pdfium_ver = int(args.pdfium_ver)
    
    with ArtifactStash():
        main_pypi(args)


if __name__ == '__main__':
    main()
