# SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("AutoCastable", "AutoCloseable", "DEBUG_AUTOCLOSE", "LIBRARY_AVAILABLE")

import os
import sys
import enum
import uuid
import weakref
import logging

logger = logging.getLogger(__name__)

class _Mutable:
    
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return f"_Mutable({self.value})"
    
    def __bool__(self):
        return bool(self.value)

DEBUG_AUTOCLOSE = _Mutable(False)
LIBRARY_AVAILABLE = _Mutable(False)  # set to true on library init

class _STATE (enum.Enum):
    INVALID  = -1
    AUTO     = 0
    EXPLICIT = 1
    BYPARENT = 2


class AutoCastable:
    
    @property
    def _as_parameter_(self):
        if self.raw is None:
            raise RuntimeError("Cannot use closed object as C function parameter.")
        return self.raw


def _close_template(close_func, raw, obj_repr, state, parent, *args, **kwargs):
    
    if DEBUG_AUTOCLOSE:
        # use os.write() rather than print() to avoid "reentrant call" exceptions on shutdown (see https://stackoverflow.com/q/75367828/15547292)
        os.write(sys.stderr.fileno(), f"Close ({state.value.name.lower()}) {obj_repr}\n".encode())
    
    if not LIBRARY_AVAILABLE:
        os.write(sys.stderr.fileno(), f"-> Cannot close object; library is destroyed. This may cause a memory leak!\n".encode())
        return
    
    assert state.value != _STATE.INVALID
    assert parent is None or not parent._tree_closed()
    close_func(raw, *args, **kwargs)


class AutoCloseable (AutoCastable):
    
    def __init__(self, close_func, *args, obj=None, needs_free=True, **kwargs):
        
        # proactively prevent accidental double initialization
        assert not hasattr(self, "_finalizer")
        
        self._close_func = close_func
        self._obj = self if obj is None else obj
        self._uuid = uuid.uuid4()
        self._ex_args = args
        self._ex_kwargs = kwargs
        self._autoclose_state = _Mutable(_STATE.AUTO)
        
        self._finalizer = None
        self._kids = []
        if needs_free:
            self._attach_finalizer()
    
    
    def __repr__(self):
        return f"<{type(self).__name__} uuid:{str(self._uuid)[:8]}>"
    
    
    def _attach_finalizer(self):
        # NOTE this function captures the value of the `parent` property at finalizer installation time
        assert self._finalizer is None
        self._finalizer = weakref.finalize(self._obj, _close_template, self._close_func, self.raw, repr(self), self._autoclose_state, self.parent, *self._ex_args, **self._ex_kwargs)
    
    def _detach_finalizer(self):
        self._finalizer.detach()
        self._finalizer = None
    
    def _tree_closed(self):
        if self.raw is None:
            return True
        if self.parent != None and self.parent._tree_closed():
            return True
        return False
    
    def _add_kid(self, k):
        self._kids.append( weakref.ref(k) )
    
    
    def close(self, _by_parent=False):
        
        # TODO remove object from parent's kids cache on finalization to avoid unnecessary accumulation
        # -> pre-requisite would be to handle kids inside finalizer, but IIRC there was some weird issue with that?
        # TODO invalidate self.raw if closing object without finalizer to prevent access after a lifetime-managing parent is closed
        
        if not self.raw or not self._finalizer:
            return False
        
        for k_ref in self._kids:
            k = k_ref()
            if k and k.raw:
                k.close(_by_parent=True)
        
        self._autoclose_state.value = _STATE.BYPARENT if _by_parent else _STATE.EXPLICIT
        self._finalizer()
        self._autoclose_state.value = _STATE.INVALID
        self.raw = None
        self._finalizer = None
        self._kids.clear()
        
        return True
