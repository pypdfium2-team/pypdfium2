# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import shutil
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from pypdfium2_setup.base import (
    ProjectDir, DataDir, DataDir_Bindings
)


def main():
    
    parser = argparse.ArgumentParser(
        description = "List/collect build licenses, assuming a prior run of update.py",
    )
    parser.add_argument(
        "--copy",
        action = "store_true",
        help = "Collect licenses into //BUILD_LICENSES_tmp directory",
    )
    args = parser.parse_args()
    
    data_dirs = [p for p in DataDir.iterdir() if p.is_dir()]
    data_dirs.remove(DataDir_Bindings)
    data_dirs.remove(DataDir/"sourcebuild")
    
    licenses = {}
    for dir in data_dirs:
        for file in (dir/"BUILD_LICENSES").iterdir():
            if file.name in licenses:
                licenses[file.name].append(dir.name)
            else:
                licenses[file.name] = [dir.name]
    
    for license, platforms in licenses.items():
        print(license)
        print(f"    {platforms}")
        print()
    
    if args.copy:
        dest_dir = ProjectDir/"BUILD_LICENSES_tmp"
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        dest_dir.mkdir()
        
        for license, platforms in licenses.items():
            shutil.copyfile(DataDir/platforms[0]/"BUILD_LICENSES"/license, dest_dir/license)


if __name__ == "__main__":
    main()
