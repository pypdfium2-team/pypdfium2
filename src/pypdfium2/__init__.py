# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2._library_scope
from pypdfium2.version import *
from pypdfium2._helpers import *
from pypdfium2 import raw, internal

# Export font initialization function
from pypdfium2._library_scope import initialize_with_fonts

# Basic __all__ - will be expanded by other modules as needed
__all__ = [
    'initialize_with_fonts',
]

# Ensure the function is available at module level
import sys
current_module = sys.modules[__name__]
current_module.initialize_with_fonts = initialize_with_fonts
