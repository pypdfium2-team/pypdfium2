# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# see https://gist.github.com/mara004/6915e904797916b961e9c53b4fc874ec for alternative approaches to deferred imports

__all__ = ("PIL_Image", "numpy")

import sys
import logging
import importlib
import functools

logger = logging.getLogger(__name__)

if sys.version_info < (3, 8):  # pragma: no cover
    # NOTE alternatively, we could write our own cached property backport with python's descriptor protocol
    def cached_property(func):
        return property( functools.lru_cache(maxsize=1)(func) )
else:
    cached_property = functools.cached_property


class _DeferredModule:
    # This is a simple deferred object proxy.
    # TODO: use the lazy_object_proxy module, if installed?
    
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


PIL_Image = _DeferredModule("PIL.Image")
numpy     = _DeferredModule("numpy")

# add setattr after we have initialized the modpaths
def _setattr_impl(self, k, v):
    return setattr(self._module, k, v)
_DeferredModule.__setattr__ = _setattr_impl
