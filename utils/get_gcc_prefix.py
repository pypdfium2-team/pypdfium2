# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Simple shim for use within cibuildwheel

import subprocess

proc = subprocess.run(["uname", "-m"], stdout=subprocess.PIPE)
arch = proc.stdout.decode().strip()
if arch == "loongarch64":
    prefix = f"{arch}-unknown-linux-gnu"
elif arch == "armv7l":
    prefix = f"arm-linux-gnueabihf"
else:
    prefix = f"{arch}-linux-gnu"

print(prefix)
