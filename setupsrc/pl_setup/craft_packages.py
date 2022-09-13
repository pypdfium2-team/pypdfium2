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


def run_build(args):
    run_cmd([sys.executable, "-m", "build", "--skip-dependency-check", "--no-isolation"] + args, cwd=SourceTree, env=os.environ)


def main():
    
    parser = argparse.ArgumentParser(
        description = "Craft sdist and wheels for pypdfium2, using `python3 -m build`. (This script does not take any arguments.)",
    )
    args = parser.parse_args()
    
    # Push possible in-tree artefacts from editable install to stash
    tmp_dir = None
    platfiles = (
        join(ModuleDir, BindingsFileName),
        join(ModuleDir, LibnameForSystem[Host.system]),
    )
    if any(os.path.exists(fp) for fp in platfiles):
        tmp_dir = tempfile.TemporaryDirectory(prefix="pypdfium2_artefact_stash_")
        for fp in platfiles:
            shutil.move(fp, tmp_dir.name)
    
    clean_artefacts()
    os.environ[BinaryTargetVar] = BinaryTarget_None
    run_build(["--sdist"])
    clean_artefacts()
    
    for plat in BinaryPlatforms:
        os.environ[BinaryTargetVar] = plat
        run_build(["--wheel"])
        clean_artefacts()
    
    # Pop stash
    if tmp_dir is not None:
        for fn in os.listdir(tmp_dir.name):
            shutil.move(join(tmp_dir.name, fn), ModuleDir)
        tmp_dir.cleanup()


if __name__ == '__main__':
    main()
