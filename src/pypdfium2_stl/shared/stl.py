# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

class cached_property:
    """
    Custom cached property implementation.
    
    Powered by the descriptor protocol. Zero overhead after the property has been loaded.
    Similar to functools.cached_property, but cleaner and more backward compatible.
    
    Note:
        Descriptor-based cached properties are inherently incompatible with slotted classes (``__slots__``), as they do not allow for instance-level shadowing of class-level attributes, which however is essential to this cached property model.
        With slots, you need to take a different approach that does not work with a decorator API: Add the property names to your slots and implement a ``__getattr__`` method which dispatches the cached property functions through a map or similar and assigns the result to the object. This is also overhead-free after load.
    
    Warning:
        Don't be tempted to think you could replace :class:`.cached_property` by stacking :class:`property` and :func:`functools.lru_cache`. You cannot. LRU cache operates on class level, not instance level, which has a ton of negative though not immediately obvious implications.
        When setting a maxsize, caches will be lost once there are more instance objects. E.g. with maxsize=1 only one instance object (the most recently used) can have a cache, whereas any other cached values are silently lost and re-created on access. Without a maxsize, the cache will grow indefinitely, and mind the strong references causing your values to never be garbage collected! There are more implications, e.g. lru_cache uses hashing, so your classes must be hashable, etc.
    """
    
    def __init__(self, func):
        self.func = func
        self.assigned_name = None
        self.__doc__ = func.__doc__
    
    # Optional. On older Python versions (< 3.6) that do not call this hook, the func's __name__ will be used as fallback.
    def __set_name__(self, cls, name):
        if self.assigned_name is None:
            self.assigned_name = name
        else:
            assert name == self.assigned_name, f"A cached property is tied to one attribute. You cannot assign to both {name!r} and {self.assigned_name!r}."
    
    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        value = self.func(obj)
        name = self.assigned_name or self.func.__name__
        setattr(obj, name, value)
        return value
