# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
import pypdfium2._pypdfium as pdfium


class ArrayFSFloat4 (ctypes.Array):
    _type_ = pdfium.FS_FLOAT
    _length_ = 4
