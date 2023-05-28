# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import shutil
import argparse
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
# TODO? consider glob import or dotted access
from pypdfium2_setup.packaging_base import (
    run_cmd,
    clean_platfiles,
    Host,
    ModuleDir,
    BindingsFileName,
    LibnameForSystem,
    BinaryPlatforms,
    SourceTree,
    BinaryTargetVar,
    BinaryTarget_None,
)


class ArtefactStash:
    
    # Preserve in-tree aftefacts from editable install
    
    def __init__(self):
        
        self.tmpdir = None
        file_names = [BindingsFileName, LibnameForSystem[Host.system]]
        self.files = [fp for fp in [ModuleDir / fn for fn in file_names] if fp.exists()]
        
        if len(self.files) == 0:
            return
        elif len(self.files) != 2:
            print(f"Warning: Expected exactly 2 platform files, but found {len(self.files)}.", file=sys.stderr)
        
        self.tmpdir = tempfile.TemporaryDirectory(prefix="pypdfium2_artefact_stash_")
        self.tmpdir_path = Path(self.tmpdir.name)
        for fp in self.files:
            shutil.move(fp, self.tmpdir_path)
    
    def pop(self):
        if self.tmpdir is None:
            return
        for fp in self.files:
            shutil.move(self.tmpdir_path / fp.name, ModuleDir)
        self.tmpdir.cleanup()


def run_build(args):
    run_cmd([sys.executable, "-m", "build", "--skip-dependency-check", "--no-isolation"] + args, cwd=SourceTree, env=os.environ)


def main():
    
    parser = argparse.ArgumentParser(
        description = "Craft sdist and wheels for pypdfium2, using `python3 -m build`. (This script does not take any arguments.)",
    )
    parser.parse_args()
    
    stash = ArtefactStash()
    
    os.environ[BinaryTargetVar] = BinaryTarget_None
    run_build(["--sdist"])
    clean_platfiles()
    
    for plat in BinaryPlatforms:
        os.environ[BinaryTargetVar] = plat
        run_build(["--wheel"])
        clean_platfiles()
    
    stash.pop()


if __name__ == '__main__':
    main()
