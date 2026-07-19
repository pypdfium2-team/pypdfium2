# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

class cached_property:
    """
    Custom cached property implementation.
    To clear a cached property from an object, simply ``del`` it (e.g. ``del obj.name``).
    
    .. note::
        
        Though this implementation does not explicitly access ``__dict__``, attempts to use cached_property in a slotted class will fail just as the stdlib's, because attributes of a slotted class cannot be shadowed on instance level, which is essential for a decorator-based cached property that should assume zero overhead after the initial access.
        
        While this is a limitation of Python's ``__slots__`` feature, you may be able to achieve the same goal through a different approach.
        Your best bet is probably to implement a ``__getattr__`` method with a table of cached property names and functions, and add the names to the slots.
        This should also be overhead-free, since once the slot is assigned ``__getattr__`` is no longer called, and you can use ``del`` likewise to unassign the slot and reroute access to ``__getattr__``.
    """
    
    def __init__(self, func):
        self.func = func
        self.assigned_name = None
        self.__doc__ = func.__doc__
    
    # Optional. On older Python versions that do not call this hook, the func's __name__ will be used as fallback.
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
