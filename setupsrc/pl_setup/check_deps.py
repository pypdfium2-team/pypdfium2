#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import shutil


Commands = (
    "git",
    "gcc",
    "ctypesgen",
)

def main():
    missing = {cmd for cmd in Commands if not shutil.which(cmd)}
    if len(missing) > 0:
        raise RuntimeError("The following packages or commands are missing: %s" % missing)


if __name__ == "__main__":
    main()
