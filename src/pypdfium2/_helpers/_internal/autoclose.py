# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ["AutoCloseable"]

import sys
import uuid
import weakref
import logging

logger = logging.getLogger(__name__)

DEBUG_AUTOCLOSE = False


class AutoCloseable:
    
    def __init__(self, close_func, *args, obj=None, needs_free=True, **kwargs):
        
        assert not hasattr(self, "_uuid")
        self._uuid = uuid.uuid4()
        
        if obj is None:
            obj = self
        
        self._fin_args = (obj, AutoCloseable._close_template, self.raw, self._uuid, self.parent, close_func, *args)
        self._fin_kwargs = kwargs
        
        self._finalizer = None
        if needs_free:
            self._attach_finalizer()
    
    
    def __bool__(self):
        # auto-closeable objects should always evaluate true
        return True
    
    @property
    def parent(self):
        return None
    
    
    def _attach_finalizer(self):
        assert self._finalizer is None
        self._finalizer = weakref.finalize(*self._fin_args, **self._fin_kwargs)
    
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
    def _close_template(raw, uuid, parent, close_func, *args, **kwargs):
        # NOTE deliberately not using logging so that it also works during the shutdown phase
        if DEBUG_AUTOCLOSE:
            print("Closing %s with UUID %s" % (raw, uuid), file=sys.stderr)
        if (parent is not None) and parent._tree_closed():
            print("Parent closed before child - this is illegal (%s, %s)." % (parent, raw), file=sys.stderr)
        close_func(raw, *args, **kwargs)
    
    
    def close(self):
        if (self.raw is None):
            logger.warning("Duplicate close call suppressed on %s." % (self, ))
            return
        if self._finalizer is not None:
            self._finalizer()
            self.raw = None
