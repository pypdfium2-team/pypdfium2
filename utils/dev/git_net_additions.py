# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Augment git diff --numstat with a net additions column and sort

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]/"setupsrc"))
from shared_base import ProjectDir

proc = subprocess.run(["git", "diff", "--numstat", sys.argv[1], sys.argv[2]], cwd=ProjectDir, stdout=subprocess.PIPE)
raw_output = proc.stdout.decode().strip()

info = {}
total = 0
for line in raw_output.splitlines():
    additions, deletions, filepath = line.strip().split("\t")
    additions, deletions = int(additions), int(deletions)
    net_additions = additions - deletions
    total += net_additions
    info[filepath] = (net_additions, additions, deletions)

# TODO use itemgetter?
info = sorted(info.items(), key=lambda entry: entry[1][0], reverse=True)
for filepath, stats in info:
    print(*stats, filepath, sep="\t")
print("-----")
print(f"{total:+}")
