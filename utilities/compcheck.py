#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import subprocess


problematic = ("pathlib", 'f"', "f'")

def main():
    for string in problematic:
        command = [
            "grep",
            "-r",
            string,
            "--include",
            "*.py",
            "--exclude-dir",
            "sourcebuild",
            "--exclude-dir",
            "data",
        ]
        print(" ".join(command))
        subprocess.run(command, cwd=os.getcwd())
        print()


if __name__ == '__main__':
    main()
