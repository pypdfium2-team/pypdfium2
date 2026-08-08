# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("ProjectDir", "log", "get_cool_date")

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

ProjectDir = Path(__file__).resolve().parents[1]

def log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

def get_cool_date(cooldown_days):
    return (datetime.now(timezone.utc) - timedelta(days=cooldown_days)).isoformat(timespec='seconds')
