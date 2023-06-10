# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("AutoCastable", "AutoCloseable", "set_autoclose_debug")

import sys
import ctypes
import weakref
import logging
import uuid

logger = logging.getLogger(__name__)

DEBUG_AUTOCLOSE = False


def set_autoclose_debug(value=True):
    global DEBUG_AUTOCLOSE
    DEBUG_AUTOCLOSE = value


class AutoCastable:
    
    @property
    def _as_parameter_(self):
        return self.raw


def _close_template(close_func, raw, obj_repr, is_auto, uuid, parent, *args, **kwargs):
    if DEBUG_AUTOCLOSE:
        print(("Automatically" if is_auto.value else "Explicitly") + f" closing raw of {uuid}:{obj_repr}", file=sys.stderr)
    assert (parent is None) or not parent._tree_closed()
    close_func(raw, *args, **kwargs)


class AutoCloseable (AutoCastable):
    
    def __init__(self, close_func, *args, obj=None, needs_free=True, **kwargs):
        
        # NOTE proactively prevent accidental double initialization
        assert not hasattr(self, "_finalizer")
        
        self._close_func = close_func
        self._obj = self if obj is None else obj
        self._uuid = uuid.uuid4() if DEBUG_AUTOCLOSE else None
        self._ex_args = args
        self._ex_kwargs = kwargs
        self._will_autoclose = ctypes.c_bool(True)  # mutable bool
        
        self._finalizer = None
        self._kids = []
        if needs_free:
            self._attach_finalizer()
    
    
    def _attach_finalizer(self):
        # NOTE this function captures the value of the `parent` property at finalizer installation time - if it changes, detach the old finalizer and create a new one
        assert self._finalizer is None
        self._finalizer = weakref.finalize(self._obj, _close_template, self._close_func, self.raw, repr(self), self._will_autoclose, self._uuid, self.parent, *self._ex_args, **self._ex_kwargs)
    
    def _detach_finalizer(self):
        self._finalizer.detach()
        self._finalizer = None
    
    def _tree_closed(self):
        if self.raw is None:
            return True
        if (self.parent is not None) and self.parent._tree_closed():
            return True
        return False
    
    def _add_kid(self, k):
        self._kids.append( weakref.ref(k) )
    
    
    def close(self):
        
        if not self.raw or not self._finalizer:
            return False
        
        for k_ref in self._kids:
            k = k_ref()
            if k and k.raw:
                k.close()
        
        self._will_autoclose.value = False
        self._finalizer()
        self._will_autoclose = None
        self.raw = None
        self._finalizer = None
        self._kids.clear()
        
        return True
