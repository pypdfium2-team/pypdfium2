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
    PlatformNames,
    AllPlatNames,
    SourceTree,
    SetupTargetVar,
)


def _run_build(args):
    run_cmd([sys.executable, "-m", "build", "--skip-dependency-check", "--no-isolation"] + args, cwd=SourceTree, env=os.environ)


def main():
    
    # This script cleans up any artefacts in src/ and currently does not restore them
    # i. e. if you were using an editable install, you'll have to re-run it (or emplace the artefacts manually)
    
    parser = argparse.ArgumentParser(
        description = "Craft sdist and wheels for pypdfium2, using `python3 -m build`. (This script does not take any arguments.)",
    )
    args = parser.parse_args()
    
    pl_names = AllPlatNames.copy()
    pl_names.remove(PlatformNames.sourcebuild)
    
    clean_artefacts()
    os.environ[SetupTargetVar] = "sdist"
    _run_build(["--sdist"])
    clean_artefacts()
    
    for plat in pl_names:
        os.environ[SetupTargetVar] = plat
        _run_build(["--wheel"])
        clean_artefacts()


if __name__ == '__main__':
    main()
