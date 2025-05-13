# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
from pypdfium2_setup.base import DataDir, DataDir_Bindings


def main():
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


if __name__ == "__main__":
    main()
