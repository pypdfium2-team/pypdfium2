# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pkg_resources
import pypdfium2 as pdfium
from pypdfium2._version import (
    V_PYPDFIUM2,
    V_LIBPDFIUM,
)


def _get_pkg_version(pkgname):
    return pkg_resources.get_distribution(pkgname).version


def test_version_aliases():
    assert pdfium.__version__ == V_PYPDFIUM2 == _get_pkg_version('pypdfium2')
    assert pdfium.__pdfium_version__ == V_LIBPDFIUM
