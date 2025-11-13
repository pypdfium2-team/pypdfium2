# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
from pathlib import Path
from copy import copy

sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from _buildbase import bootstrap_gn

argv = copy(sys.argv[1:])
if len(argv) > 0:
    argv[0] = Path(argv[0])
bootstrap_gn(*argv, skip_if_present=False)
