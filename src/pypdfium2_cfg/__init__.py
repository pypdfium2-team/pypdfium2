# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

class _Mutable:
    
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return f"_Mutable({self.value})"
    
    def __bool__(self):
        return bool(self.value)


DEBUG_AUTOCLOSE = _Mutable(False)
