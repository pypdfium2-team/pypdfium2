# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# See also
# https://gist.github.com/mara004/f2926b1fcc8847a69e0af6f4e33934fd (comments)
# https://gist.github.com/mara004/1170f7bfb0fb6fd8dd1e9872696c2d4e
# https://stackoverflow.com/a/78825819/15547292

class cached_property:
    """
    Custom cached property implementation.
    
    Powered by the descriptor protocol. Zero overhead after the property has been loaded.
    Similar to :obj:`functools.cached_property`, but cleaner and more backward compatible.
    
    Note:
        Descriptor-based cached properties are inherently incompatible with ``__slots__``, as slotted classes do not allow for instance-level shadowing of class-level attributes, which however is essential for this cached property model.\n
        With slots, you need to take a different approach that does not work with a decorator API: Add the property names to your slots and implement a ``__getattr__`` method which dispatches the cached property functions through a map or similar, and assigns the result to the object. This is also overhead-free after load.
    
    Important:
        Don't be tempted to think :class:`.cached_property` could be replaced (or backported) by stacking :class:`property` and :func:`functools.lru_cache`. It cannot.
        :func:`~functools.lru_cache` operates on class level, not instance level, which has a ton of negative implications.
        
        In particular, when there are more instance objects than ``maxsize``, caches would be lost, whereas an unbounded class-level cache would never be cleared.
        Cached properties belong to instance level so that cached values remain with their objects, and eventually get garbage collected together.
        
        In general, you almost never want :func:`functools.lru_cache` except on standalone functions. It is inappropriate on methods. Unfortunately, there is no instance-level LRU cache in the standard library, but you could consider something like ``methodtools.lru_cache()``.
    """
    
    def __init__(self, func):
        self.func = func
        self.assigned_name = None
        self.__doc__ = func.__doc__
    
    def __set_name__(self, cls, name):
        if self.assigned_name is None:
            self.assigned_name = name
        else:
            assert name == self.assigned_name, f"A cached property is tied to one attribute. You cannot assign to both {name!r} and {self.assigned_name!r}."
    
    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        value = self.func(obj)
        name = self.assigned_name  # or self.func.__name__ (py < 3.6)
        setattr(obj, name, value)
        return value
