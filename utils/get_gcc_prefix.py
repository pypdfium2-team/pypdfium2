# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Simple shim for use within cibuildwheel and sbuild_one.yaml

import os, sys

def main(arch=None):
    if not arch:
        arch = os.uname().machine
    if arch == "loongarch64":
        return f"{arch}-unknown-linux-gnu"
    elif arch in ("armv7l", "armv8l"):
        return "arm-linux-gnueabihf"
    elif arch == "ppc64le":
        return "powerpc64le-linux-gnu"
    else:
        return f"{arch}-linux-gnu"

def main_cli(argv=sys.argv[1:]):
    arch = argv[0] if len(argv) > 0 else None
    print(main(arch))

if __name__ == '__main__':
    main_cli()
