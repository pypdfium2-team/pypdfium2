# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import shutil
import argparse
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
# TODO consider dotted access?
from pypdfium2_setup.packaging_base import *


class ArtifactStash:
    
    # Preserve in-tree aftefacts from editable install
    
    def __init__(self):
        
        self.tmpdir = None
        
        # FIXME some degree of duplication with base::get_platfiles()
        file_names = [VersionFN, BindingsFN, LibnameForSystem[Host.system]]
        self.files = [fp for fp in [ModuleDir_Raw / fn for fn in file_names] if fp.exists()]
        if len(self.files) == 0:
            return
        elif len(self.files) != 2:
            print(f"Warning: Expected exactly 2 platform files, but found {len(self.files)}.", file=sys.stderr)
        
        self.tmpdir = tempfile.TemporaryDirectory(prefix="pypdfium2_artifact_stash_")
        self.tmpdir_path = Path(self.tmpdir.name)
        for fp in self.files:
            shutil.move(fp, self.tmpdir_path)
    
    def pop(self):
        if self.tmpdir is None:
            return
        for fp in self.files:
            shutil.move(self.tmpdir_path / fp.name, ModuleDir_Raw)
        self.tmpdir.cleanup()


def run_build(args):
    run_cmd([sys.executable, "-m", "build", "--skip-dependency-check", "--no-isolation"] + args, cwd=ProjectDir, env=os.environ)


def main():
    
    parser = argparse.ArgumentParser(
        description = "Craft sdist and wheels for pypdfium2, using `python3 -m build`.",
    )
    parser.add_argument(
        "--use-v8",
        action = "store_true",
    )
    parser.add_argument(
        "--version",
        type = int,
        default = None,
    )
    args = parser.parse_args()
    if not args.version:
        args.version = PdfiumVer.get_latest()
    
    stash = ArtifactStash()
    
    os.environ[PlatSpec_EnvVar] = PlatTarget_None
    run_build(["--sdist"])
    clean_platfiles()
    
    suffix = (PlatSpec_V8Sym if args.use_v8 else "") + PlatSpec_VerSep + str(args.version)
    for plat in BinaryPlatforms:
        os.environ[PlatSpec_EnvVar] = plat + suffix
        run_build(["--wheel"])
        clean_platfiles()
    
    stash.pop()


if __name__ == '__main__':
    main()
