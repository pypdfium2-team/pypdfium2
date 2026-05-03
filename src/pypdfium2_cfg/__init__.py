# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import logging


class _Mutable:
    
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return f"{type(self).__name__}({self.value})"
    
    def __bool__(self):
        return bool(self.value)

class _MutableLoglevel (_Mutable):
    def __bool__(self):  # bw compat
        return self.value < logging.WARNING

DEBUG_AUTOCLOSE = _MutableLoglevel(logging.WARNING)
