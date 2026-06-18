# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys, shlex

def get_gcc_id(arch):
    if arch in ("armv7l", "armv8l"):
        return "arm-linux-gnueabihf"
    elif arch == "ppc64le":
        return "powerpc64le-linux-gnu"
    elif arch == "mips64el":
        return "mips64el-linux-gnuabi64"
    # elif arch in ("loong64", "loongarch64"):
    #     return "loongarch64-unknown-linux-gnu"
    else:  # aarch64, (riscv64)
        return f"{arch}-linux-gnu"

target_cpu = sys.argv[1]
host_os = sys.argv[2] if len(sys.argv) > 2 else None
deps = []

if target_cpu == "x86":
    deps.append("g++-multilib")
else:
    uname_cpu = {
        "arm": "armv7l",
        "arm64": "aarch64",
        "ppc64": "ppc64le",
    }.get(target_cpu, target_cpu)
    gcc_ver = {
        "ubuntu-24.04": 14,
        "ubuntu-26.04": 16,
    }.get(host_os, 14)
    gcc_id = get_gcc_id(uname_cpu)
    gcc_suffix = f"{gcc_ver}-{gcc_id}"
    deps += ("libc6-i386", f"gcc-{gcc_ver}-multilib", f"g++-{gcc_suffix}", f"gcc-{gcc_suffix}")

print(" ".join(shlex.quote(d) for d in deps))
