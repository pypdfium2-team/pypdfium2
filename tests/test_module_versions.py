# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pkg_resources
from pypdfium2 import V_PYPDFIUM2, V_LIBPDFIUM


def test_versions():
    assert V_PYPDFIUM2 == pkg_resources.get_distribution('pypdfium2').version
    assert V_LIBPDFIUM > 5000
