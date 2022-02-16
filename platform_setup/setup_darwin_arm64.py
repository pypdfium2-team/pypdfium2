#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from platform_setup.setup_base import mkwheel
from platform_setup.packaging_base import PlatformDirs

mkwheel(PlatformDirs.DarwinArm64)
