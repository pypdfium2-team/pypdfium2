# SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("AutoCastable", "AutoCloseable", "DEBUG_AUTOCLOSE", "LIBRARY_AVAILABLE")

import os
import sys
import ctypes
import weakref
import logging
import uuid

logger = logging.getLogger(__name__)

# mutable bools
DEBUG_AUTOCLOSE = ctypes.c_bool(False)
LIBRARY_AVAILABLE = ctypes.c_bool(False)  # set to true on library init

STATE_INVALID = -1
STATE_AUTO = 0
STATE_EXPLICIT = 1
STATE_BYPARENT = 2


class AutoCastable:
    
    @property
    def _as_parameter_(self):
        return self.raw


def _close_template(close_func, raw, obj_repr, state, parent, *args, **kwargs):
    
    if DEBUG_AUTOCLOSE:
        desc = {STATE_AUTO: "auto", STATE_EXPLICIT: "explicit", STATE_BYPARENT: "by parent"}[state.value]
        # use os.write() rather than print() to avoid "reentrant call" exceptions on shutdown (see https://stackoverflow.com/q/75367828/15547292)
        os.write(sys.stderr.fileno(), f"Close ({desc}) {obj_repr}\n".encode())
    
    if not LIBRARY_AVAILABLE:
        os.write(sys.stderr.fileno(), f"-> Cannot close object, library is destroyed. This may cause a memory leak!\n".encode())
        return
    
    assert (parent is None) or not parent._tree_closed()
    close_func(raw, *args, **kwargs)


class AutoCloseable (AutoCastable):
    
    def __init__(self, close_func, *args, obj=None, needs_free=True, **kwargs):
        
        # NOTE proactively prevent accidental double initialization
        assert not hasattr(self, "_finalizer")
        
        self._close_func = close_func
        self._obj = self if obj is None else obj
        self._uuid = uuid.uuid4()
        self._ex_args = args
        self._ex_kwargs = kwargs
        self._autoclose_state = ctypes.c_int8(STATE_AUTO)  # mutable int
        
        self._finalizer = None
        self._kids = []
        if needs_free:
            self._attach_finalizer()
    
    
    def __repr__(self):
        return f"<{type(self).__name__} uuid:{str(self._uuid)[:8]}>"
    
    
    def _attach_finalizer(self):
        # NOTE this function captures the value of the `parent` property at finalizer installation time - if it changes, detach the old finalizer and create a new one
        assert self._finalizer is None
        self._finalizer = weakref.finalize(self._obj, _close_template, self._close_func, self.raw, repr(self), self._autoclose_state, self.parent, *self._ex_args, **self._ex_kwargs)
    
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
    
    
    def close(self, _by_parent=False):
        
        if not self.raw or not self._finalizer:
            return False
        
        for k_ref in self._kids:
            k = k_ref()
            if k and k.raw:
                k.close(_by_parent=True)
        
        self._autoclose_state.value = STATE_BYPARENT if _by_parent else STATE_EXPLICIT
        self._finalizer()
        self._autoclose_state.value = STATE_INVALID
        self.raw = None
        self._finalizer = None
        self._kids.clear()
        
        return True
