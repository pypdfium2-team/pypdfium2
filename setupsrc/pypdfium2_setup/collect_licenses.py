# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from pypdfium2_setup.base import (
    ProjectDir, DataDir, DataDir_Bindings
)


def main():
    
    first_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if first_arg in ("-h", "--help"):
        print(f"Run {sys.argv[1]} without arguments to list licenses, or with 'copy' to collect licenses into //BUILD_LICENSES. Note: This assumes a prior run of update.py")
    do_collect = first_arg == "copy"
    
    data_dirs = [p for p in DataDir.iterdir() if p.is_dir()]
    data_dirs.remove(DataDir_Bindings)
    
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
    
    if do_collect:
        dest_dir = ProjectDir/"BUILD_LICENSES"
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        dest_dir.mkdir()
        
        for license, platforms in licenses.items():
            shutil.copyfile(DataDir/platforms[0]/"BUILD_LICENSES"/license, dest_dir/license)


if __name__ == "__main__":
    main()
