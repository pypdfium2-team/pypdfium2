# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pl_setup.packaging_base import PlatformNames


def test_platformnames():
    for member in dir(PlatformNames):
        if member.startswith('_'):
            continue
        assert member == getattr(PlatformNames, member)
