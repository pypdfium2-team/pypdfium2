# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

class cached_property:
    """
    Custom cached property implementation.
    To clear a cached property from an object, simply ``del`` it (e.g. ``del obj.name``).
    
    .. note::
        Although this implementation does not explicitly access ``__dict__``, attempts to use cached_property in a slotted class will fail just as the stdlib's, because attributes of a slotted class cannot be shadowed on instance level, which is essential for any zero-overhead cached property implementation.
    """
    
    def __init__(self, func):
        self.func = func
        self.assigned_name = None
        self.__doc__ = getattr(func, "__doc__", None)
    
    # Optional. On older Python versions that do not call this hook, the func's __name__ wil be used as fallback.
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
