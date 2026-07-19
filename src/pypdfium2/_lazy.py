# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# see https://gist.github.com/mara004/6915e904797916b961e9c53b4fc874ec for alternative approaches to deferred imports

import sys
import logging

logger = logging.getLogger(__name__)


class cached_property:
    """
    Custom cached property implementation.
    To clear a cached property from an object, simply `del` it (e.g. `del obj.name`).
    
    .. note::
        Although this implementation does not explicitly access __dict__, attempts to use cached_property in a slotted class will fail just as the stdlib's, because attributes of a slotted class cannot be shadowed on instance level, which is essential for any zero-overhead cached property implementation.
    """
    
    def __init__(self, func):
        self.func = func
        self.assigned_name = None
        self.__doc__ = func.__doc__
    
    if sys.version_info >= (3, 6):
        def __set_name__(self, owner, name):
            if self.assigned_name is None:
                self.assigned_name = name
            else:
                assert name == self.assigned_name, f"A cached property is tied to one attribute. You cannot assign to both {name!r} and {self.assigned_name!r}."
    
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        value = self.func(instance)
        name = self.assigned_name or self.func.__name__
        setattr(instance, name, value)
        return value


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
