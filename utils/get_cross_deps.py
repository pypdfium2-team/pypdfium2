# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys, shlex

def get_gcc_id(arch):
    if arch in ("armv7l", "armv8l"):
        return "arm-linux-gnueabihf"
    elif arch == "ppc64le":
        return "powerpc64le-linux-gnu"
    # elif arch in ("loong64", "loongarch64"):
    #     return "loongarch64-unknown-linux-gnu"
    else:  # aarch64, (riscv64)
        return f"{arch}-linux-gnu"

target_cpu = sys.argv[1]
deps = []

if target_cpu == "x86":
    deps += ["g++-multilib"]
else:
    uname_cpu = {
        "arm": "armv7l",
        "arm64": "aarch64",
        "ppc64": "ppc64le",
    }.get(target_cpu, target_cpu)
    gcc_id = get_gcc_id(uname_cpu)
    deps += ["libc6-i386", "gcc-10-multilib", f"g++-10-{gcc_id}", f"gcc-10-{gcc_id}"]

print(" ".join(shlex.quote(d) for d in deps))
