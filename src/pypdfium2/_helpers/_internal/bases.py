# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ["AutoCastable", "AutoCloseable", "set_autoclose_debug"]

import sys
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


class AutoCloseable (AutoCastable):
    # auto-closeable objects should always be auto-castable
    
    def __init__(self, close_func, *args, obj=None, needs_free=True, **kwargs):
        
        # proactively prevent accidental double initialization
        assert not hasattr(self, "_finalizer")
        
        self._close_func = close_func
        self._obj = self if obj is None else obj
        self._uuid = uuid.uuid4() if DEBUG_AUTOCLOSE else None
        self._ex_args = args
        self._ex_kwargs = kwargs
        
        self._finalizer = None
        if needs_free:
            self._attach_finalizer()
    
    
    def _attach_finalizer(self):
        # this function captures the value of the `parent` property at finalizer installation time - if it changes, detach the old finalizer and create a new one
        assert self._finalizer is None
        self._finalizer = weakref.finalize(self._obj, AutoCloseable._close_template, self._close_func, self.raw, self._uuid, self.parent, *self._ex_args, **self._ex_kwargs)
    
    def _detach_finalizer(self):
        self._finalizer.detach()
        self._finalizer = None
    
    def _tree_closed(self):
        if self.raw is None:
            return True
        if (self.parent is not None) and self.parent._tree_closed():
            return True
        return False
    
    
    @staticmethod
    def _close_template(close_func, raw, uuid, parent, *args, **kwargs):
        # FIXME should we add context info (explicit/automatic) ?
        if DEBUG_AUTOCLOSE:
            print(f"Closing {raw} with UUID {uuid}", file=sys.stderr)
        # TODO add needs_parent safety check (if True, `parent` must be given)
        if (parent is not None) and parent._tree_closed():
            print(f"Parent closed before child - this is illegal ({parent}, {raw}).", file=sys.stderr)
        close_func(raw, *args, **kwargs)
    
    
    def close(self):
        # TODO? issue a warning if needs_free=False ?
        if (self.raw is None):
            logger.warning(f"Duplicate close call suppressed on {self}.")
            return
        if self._finalizer is not None:
            self._finalizer()
            self.raw = None
