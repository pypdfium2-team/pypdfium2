# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Augment `git diff --numstat` with a delta column (net additions, i.e. additions-deletions), and sort the output by that column.
# This helps maintainers analyze net growth (or degrowth) between refs on a per file basis, ordered by relevance, with the highest net additions shown first. (Author's note: AOTW, neither git itself, nor GitHub, nor any other tool I'm aware of seemed to offer that functionality.)
# For completeness, this script also adds a churn column (absolute additions+deletions) as in `git diff --stat`. Validates the final result against `git diff --shortstat`.

import sys
import subprocess
from pathlib import Path
from operator import itemgetter

ProjectDir = Path(__file__).resolve().parents[2]


class _PseudoInt (int):
    
    def __new__(cls, num, src):
        obj = super().__new__(cls, num)
        obj._src = src
        return obj
    
    def __repr__(self):
        return f'{super().__repr__()}#{self._src!r}'

def _to_int(value):
    try:
        return int(value)
    except ValueError as e:
        # Although emphasizing machine readability, git diff --numstat explicitly outputs "-" for binary files, rather than 0. Seems counter-intuitive to a parser writer (not sure why they don't indicate binary files in some other way). Anyway, that's how it is.
        return _PseudoInt(0, value)


def _git_diff(difftype):
    proc = subprocess.run(["git", "diff", difftype, sys.argv[1], sys.argv[2]], cwd=ProjectDir, stdout=subprocess.PIPE)
    return proc.stdout.decode().strip()

raw_output = _git_diff("--numstat")
info = []
for line in raw_output.splitlines():
    a, d, fp = line.strip().split("\t")
    a, d = _to_int(a), _to_int(d)
    info.append((a, d, a-d, a+d, fp))

print("add(+)", "del(-)", "delta", "churn", "file", sep="\t")
print("-" * 75)

info.sort(key=itemgetter(2), reverse=True)
for a, d, delta, churn, fp in info:
    print(a, d, f"{delta:+}", churn, fp, sep="\t")

num_cols = zip(*(n for *n, fp in info))
t_add, t_del, t_delta, t_churn = tuple(sum(c) for c in num_cols)
print("-" * 75)
print(f"+{t_add}", f"-{t_del}", f"{t_delta:+}", t_churn, len(info), sep="\t")

# sanity check
raw_shortstat = _git_diff("--shortstat")
n_files, c_add, c_del = tuple(int(p.split(" ")[0]) for p in raw_shortstat.split(", "))
assert t_delta == t_add - t_del
assert t_churn == t_add + t_del
assert (c_add, c_del) == (t_add, t_del)
assert n_files == len(info)
