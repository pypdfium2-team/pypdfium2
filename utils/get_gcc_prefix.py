# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Simple shim for use within cibuildwheel and sbuild_one.yaml

import sys, subprocess

def main(arch=None):
    
    if not arch:
        proc = subprocess.run(["uname", "-m"], stdout=subprocess.PIPE)
        arch = proc.stdout.decode().strip()

    if arch == "loongarch64":
        prefix = f"{arch}-unknown-linux-gnu"
    elif arch == "armv7l":
        prefix = f"arm-linux-gnueabihf"
    else:
        prefix = f"{arch}-linux-gnu"

    return prefix

def main_cli(argv=sys.argv[1:]):
    arch = argv[0] if len(argv) > 0 else None
    print(main(arch))

if __name__ == '__main__':
    main_cli()
