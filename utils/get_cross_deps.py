# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import get_gcc_prefix  # local
import shlex

target_cpu = sys.argv[1]
deps = []

if target_cpu == "x86":
    deps += ["g++-multilib"]
else:
    gcc_cpu = {"arm": "armv7l", "arm64": "aarch64"}[target_cpu]
    gcc_id = get_gcc_prefix.main(gcc_cpu)
    deps += ["libc6-i386", "gcc-10-multilib", f"g++-10-{gcc_id}", f"gcc-10-{gcc_id}"]

print(" ".join(shlex.quote(d) for d in deps))
