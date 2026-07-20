# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# see https://gist.github.com/mara004/6915e904797916b961e9c53b4fc874ec for alternative approaches to deferred imports

import logging
from pypdfium2_stl import cached_property

logger = logging.getLogger(__name__)

class _LazyClass:
    
    @cached_property
    def PIL_Image(self):
        logger.debug("Evaluating lazy import 'PIL.Image' ...")
        import PIL.Image; return PIL.Image
    
    @cached_property
    def numpy(self):
        logger.debug("Evaluating lazy import 'numpy' ...")
        import numpy; return numpy
    
    @cached_property
    def tabulate(self):
        # logger.debug("Evaluating lazy import 'tabulate' ...")
        from tabulate import tabulate; return tabulate

Lazy = _LazyClass()
