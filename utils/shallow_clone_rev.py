# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from base import git_clone_rev

url, rev, target_dir = sys.argv[1:4]
target_dir = Path(target_dir)
git_clone_rev(url, rev, target_dir, depth=1)
