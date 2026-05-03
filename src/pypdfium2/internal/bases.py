# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("AutoCastable", "AutoCloseable", "ObjectTracker", "LIBRARY_AVAILABLE", "DEBUG_AUTOCLOSE", "_debug_close", "_warn_close")

import os
import sys
import enum
import uuid
import weakref
import logging
from collections import defaultdict
import pypdfium2_cfg
from pypdfium2._lazy import cached_property
from pypdfium2_cfg import DEBUG_AUTOCLOSE  # bw compat

logger = logging.getLogger(__name__)
LIBRARY_AVAILABLE = pypdfium2_cfg._Mutable(False)  # set to true on library init

ObjectTracker = defaultdict(set)


def _debug_close(msg, prio=logging.DEBUG):  # pragma: no cover
    # try to use os.write() rather than print() or logger.whatever() to avoid "reentrant call" or "I/O operation on closed file" exceptions on shutdown (see https://stackoverflow.com/q/75367828/15547292)
    if prio < DEBUG_AUTOCLOSE.value:
        return
    try:
        os.write(sys.stderr.fileno(), (msg+"\n").encode())
    except Exception:  # e.g. io.UnsupportedOperation
        print(msg, file=sys.stderr)

def _warn_close(msg):
    _debug_close(msg, logging.WARNING)


class _STATE (enum.Enum):
    INVALID  = -1
    AUTO     = 0
    EXPLICIT = 1
    BYPARENT = 2


# class _Dataclass:
#     
#     def _iter_fields(self):
#         for slot in self.__slots__:
#             yield getattr(self, slot)
#     
#     def __repr__(self):
#         return f"{type(self).__name__}{tuple(self._iter_fields())}"

class _FinalizerInfo:  # (_Dataclass)
    __slots__ = ("close_func", "args", "kwargs", "tracked", "state")
    def __init__(self, close_func, args, kwargs, tracked):
        self.close_func = close_func
        self.args, self.kwargs = args, kwargs
        self.tracked = tracked
        self.state = _STATE.AUTO

class _FinalizerOwner:  # (_Dataclass)
    __slots__ = ("raw", "parent", "wref", "type", "repr")
    def __init__(self, raw, parent, wref, type, repr):
        self.raw, self.parent = raw, parent
        self.wref, self.type, self.repr = wref, type, repr


def _close_template(info, owner):
    
    # This function must not pull in any strong reference to the object being finalized
    # https://docs.python.org/3/library/weakref.html#weakref.finalize
    # > It is important to ensure that func, args and kwargs do not own any references to obj, either directly or indirectly, since otherwise obj will never be garbage collected. In particular, func should not be a bound method of obj.
    
    _debug_close(f"Close ({info.state.name.lower()}) {owner.repr}")
    if not LIBRARY_AVAILABLE:  # pragma: no cover
        _warn_close(f"-> Cannot close {owner.repr}; pdfium library is destroyed. This may cause a memory leak.")
        return
    
    assert info.state != _STATE.INVALID
    
    parent = owner.parent
    if parent is not None:
        assert not parent._tree_closed()
        if info.tracked:
            assert owner.wref in parent._kids, f"{owner.repr} {owner.wref}, {parent} {parent._kids}"
            parent._kids.remove(owner.wref)
    
    info.close_func(owner.raw, *info.args, **info.kwargs)
    ObjectTracker[owner.type].remove(owner.wref)


class AutoCastable:
    
    @property
    def _as_parameter_(self):
        # trust in the caller not to invoke APIs on an object after .close()
        # if not self.raw:
        #     raise RuntimeError("bool(obj.raw) must evaluate to True for use as C function parameter")
        return self.raw
    
    @cached_property
    def _wref_to_self(self):
        return weakref.ref(self)


class AutoCloseable (AutoCastable):
    
    def __init__(self, close_func, *args, obj=None, needs_free=True, tracked=True, **kwargs):
        
        # proactively prevent accidental double initialization
        assert not hasattr(self, "_finalizer")
        
        self._fin_info = _FinalizerInfo(close_func, args, kwargs, tracked)
        self._fin_obj = self if obj is None else obj
        self._finalizer = None
        
        if needs_free:
            self._attach_finalizer()
    
    @cached_property
    def _kids(self):
        return set()
    
    @cached_property
    def _uuid(self):
        return uuid.uuid4() if DEBUG_AUTOCLOSE.value < logging.WARNING else None
    
    def __repr__(self):
        identifier = hex(id(self)) if self._uuid is None else self._uuid.hex[:14]
        return f"<{type(self).__name__} {identifier}>"
    
    def _attach_finalizer(self):
        assert self._finalizer is None
        own_type = type(self)
        # note, this captures the object's parent, repr and so on at finalizer installation time
        # in case they ever change, we'd have to store the owner in an attribute and update it
        owner = _FinalizerOwner(self.raw, self.parent, self._wref_to_self, own_type, repr(self))
        self._finalizer = weakref.finalize(self._fin_obj, _close_template, self._fin_info, owner)
        ObjectTracker[own_type].add(self._wref_to_self)
    
    def _detach_finalizer(self):
        self._finalizer.detach()
        self._finalizer = None
        ObjectTracker[type(self)].remove(self._wref_to_self)
    
    def _tree_closed(self):
        if self.raw is None:
            return True
        if self.parent != None and self.parent._tree_closed():
            return True
        return False
    
    def _add_kid(self, kid):
        # assuming kid is also AutoCloseable
        self._kids.add( kid._wref_to_self )
    
    
    def close(self, _by_parent=False):
        
        if not self.raw:
            return False
        if not self._finalizer:
            self.raw = None
            return False
        
        # only need to check this in manual closing, with finalizers the API contract promises the order of invocation
        need_close = []
        for k_wref in self._kids:
            k = k_wref()
            if k and k.raw:
                # closing a child will remove it from the parent's kids set, so again outsource the actual closing to avoid "RuntimeError: Set changed size during iteration"
                need_close.append(k)
        for k in need_close:
            k.close(_by_parent=True)
        
        if self._kids:
            logger.warning(f"Some kids weakrefs have not been cleaned up: {self._kids}")
            self._kids.clear()
        
        self._fin_info.state = _STATE.BYPARENT if _by_parent else _STATE.EXPLICIT
        self._finalizer()
        self._fin_info.state = _STATE.INVALID
        self.raw = None
        self._finalizer = None
        
        return True
