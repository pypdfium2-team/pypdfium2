# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import atexit
import logging

from ._logging import setup_logger

logger = logging.getLogger(__name__)
setup_logger(logger)

from . import _pypdfium as pdfium
from ._constants import *
from ._exceptions import *
from ._helpers import *
from ._version import V_LIBPDFIUM, V_PYPDFIUM2

__version__ = V_PYPDFIUM2
__pdfium_version__ = V_LIBPDFIUM

pdfium.FPDF_InitLibrary()


def exit_handler():
    pdfium.FPDF_DestroyLibrary()


atexit.register(exit_handler)
