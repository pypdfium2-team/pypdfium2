# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes

Py_IncRef = ctypes.pythonapi.Py_IncRef
Py_IncRef.argtypes = [ctypes.py_object]

Py_DecRef = ctypes.pythonapi.Py_DecRef
Py_DecRef.argtypes = [ctypes.py_object]
