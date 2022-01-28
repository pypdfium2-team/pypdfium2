# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# This namespace encompasses all public PyPDFium2 members

from pypdfium2._pypdfium import *
from pypdfium2._helpers import *
from pypdfium2._version import (
    V_PYPDFIUM2,
    V_LIBPDFIUM,
)

__version__ = V_PYPDFIUM2
__pdfium_version__ = V_LIBPDFIUM
