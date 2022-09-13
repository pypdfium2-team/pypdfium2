# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import argparse
from os.path import dirname, abspath

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from pl_setup.packaging_base import (
    run_cmd,
    clean_artefacts,
    BinaryPlatforms,
    SourceTree,
    BinaryTargetVar,
    BinaryTarget_None,
)


def _run_build(args):
    run_cmd([sys.executable, "-m", "build", "--skip-dependency-check", "--no-isolation"] + args, cwd=SourceTree, env=os.environ)


def main():
    
    # TODO restore in-tree artefacts from editable install
    
    parser = argparse.ArgumentParser(
        description = "Craft sdist and wheels for pypdfium2, using `python3 -m build`. (This script does not take any arguments.)",
    )
    args = parser.parse_args()
    
    clean_artefacts()
    os.environ[BinaryTargetVar] = BinaryTarget_None
    _run_build(["--sdist"])
    clean_artefacts()
    
    for plat in BinaryPlatforms:
        os.environ[BinaryTargetVar] = plat
        _run_build(["--wheel"])
        clean_artefacts()


if __name__ == '__main__':
    main()
