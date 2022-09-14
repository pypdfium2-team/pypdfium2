# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import shutil
import argparse
import tempfile
from os.path import (
    join,
    dirname,
    abspath,
)

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from pl_setup.packaging_base import (
    run_cmd,
    clean_artefacts,
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
        
        self.tmp_dir = None
        self.plfile_names = [BindingsFileName, LibnameForSystem[Host.system]]
        self.plfile_paths = [join(ModuleDir, fn) for fn in self.plfile_names]
        
        if not any(os.path.exists(fp) for fp in self.plfile_paths):
            return
        self.tmp_dir = tempfile.TemporaryDirectory(prefix="pypdfium2_artefact_stash_")
        for fp in self.plfile_paths:
            shutil.move(fp, self.tmp_dir.name)
    
    def pop(self):
        if self.tmp_dir is None:
            return
        for fn in self.plfile_names:
            shutil.move(join(self.tmp_dir.name, fn), ModuleDir)
        self.tmp_dir.cleanup()


def run_build(args):
    run_cmd([sys.executable, "-m", "build", "--skip-dependency-check", "--no-isolation"] + args, cwd=SourceTree, env=os.environ)


def main():
    
    parser = argparse.ArgumentParser(
        description = "Craft sdist and wheels for pypdfium2, using `python3 -m build`. (This script does not take any arguments.)",
    )
    args = parser.parse_args()
    
    stash = ArtefactStash()
    
    os.environ[BinaryTargetVar] = BinaryTarget_None
    run_build(["--sdist"])
    clean_artefacts()
    
    for plat in BinaryPlatforms:
        os.environ[BinaryTargetVar] = plat
        run_build(["--wheel"])
        clean_artefacts()
    
    stash.pop()


if __name__ == '__main__':
    main()
