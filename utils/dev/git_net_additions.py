# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Augment git diff --numstat with a net additions column and sort

import sys
import subprocess
from pathlib import Path

ProjectDir = Path(__file__).resolve().parents[2]

def _git_diff(difftype):
    proc = subprocess.run(["git", "diff", difftype, sys.argv[1], sys.argv[2]], cwd=ProjectDir, stdout=subprocess.PIPE)
    return proc.stdout.decode().strip()

raw_output = _git_diff("--numstat")
info = {}
for line in raw_output.splitlines():
    a, d, fp = line.strip().split("\t")
    a, d = int(a), int(d)
    info[fp] = (a-d, a, d)

print("\t".join(("delta", "add(+)", "del(-)", "file")))
print("-" * 75)

sorted_info = sorted(info.items(), key=lambda entry: entry[1][0], reverse=True)
for fp, (net, a, d) in sorted_info:
    print(f"{net:+}\t{a}\t{d}\t{fp}")

t_net, t_add, t_del = tuple(sum(col) for col in zip(*info.values()))
print("-" * 75)
print(f"{t_net:+}\t+{t_add}\t-{t_del}\t{len(info)}")

# sanity check
raw_shortstat = _git_diff("--shortstat")
n_files, c_add, c_del = tuple(int(p.split(" ")[0]) for p in raw_shortstat.split(", "))
assert t_net == t_add - t_del
assert (c_add, c_del) == (t_add, t_del)
assert n_files == len(info) == len(sorted_info)
