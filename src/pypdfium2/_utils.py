# SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# see https://gist.github.com/mara004/6915e904797916b961e9c53b4fc874ec for alternative approaches to deferred imports

import sys
import logging
import importlib
import functools

logger = logging.getLogger(__name__)

if sys.version_info < (3, 8):
    # NOTE alternatively, we could write our own cached property backport with python's descriptor protocol
    def cached_property(func):
        return property( functools.lru_cache(maxsize=1)(func) )
else:
    cached_property = functools.cached_property


class _DeferredModule:
    
    # FIXME Attribute assignment will affect only the wrapper, not the actual module.
    
    def __init__(self, modpath):
        self._modpath = modpath
    
    def __repr__(self):
        return f"<deferred module wrapper {self._modpath!r}>"
    
    @cached_property
    def _module(self):
        logger.debug(f"Evaluating deferred import {self._modpath}")
        return importlib.import_module(self._modpath)
    
    def __getattr__(self, k):
        return getattr(self._module, k)


@functools.lru_cache(maxsize=5)
def deferred_import(modpath):
    return _DeferredModule(modpath)
