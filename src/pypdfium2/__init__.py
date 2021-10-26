# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import logging
from pypdfium2 import _version
from pypdfium2._pypdfium import *
from pypdfium2._helpers import *
from pypdfium2._constants import *
from pypdfium2._exceptions import *
from pypdfium2._logging import setup_logger

__version__ = _version.V_PYPDFIUM2
__pdfium_version__ = _version.V_LIBPDFIUM

logger = logging.getLogger(__name__)
setup_logger(logger)

FPDF_InitLibrary()
