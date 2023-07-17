# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import ctypes
import pypdfium2.raw as pdfium_c


def color_tohex(color, rev_byteorder):
    
    if len(color) != 4:
        raise ValueError("Color must consist of exactly 4 values.")
    if not all(0 <= c <= 255 for c in color):
        raise ValueError("Color value exceeds boundaries.")
    
    # different color interpretation with FPDF_REVERSE_BYTE_ORDER might be a bug? at least it's not documented.
    r, g, b, a = color
    channels = (a, b, g, r) if rev_byteorder else (a, r, g, b)
    
    c_color = 0
    shift = 24
    for c in channels:
        c_color |= c << shift
        shift -= 8
    
    return c_color


def set_callback(struct, fname, callback):
    setattr(struct, fname, type( getattr(struct, fname) )(callback))


def is_buffer(buf, spec="r"):
    assert set(spec).issubset( set("rw") ) and len(spec) > 0
    ok = True
    if "r" in spec:
        ok = all(hasattr(buf, a) for a in ("seek", "tell")) and (hasattr(buf, "readinto") or hasattr(buf, "read"))
    if "w" in spec:
        ok = ok and hasattr(buf, "write")
    return ok


class _buffer_reader:
    
    def __init__(self, buffer):
        self.buffer = buffer
        self._fill = self._readinto if hasattr(self.buffer, "readinto") else self._memmove
    
    def _readinto(self, cbuf, _):
        self.buffer.readinto(cbuf)
    
    def _memmove(self, cbuf, size):
        ctypes.memmove(cbuf, self.buffer.read(size), size)
    
    def __call__(self, _, position, p_buf, size):
        cbuf = ctypes.cast(p_buf, ctypes.POINTER(ctypes.c_char * size)).contents
        self.buffer.seek(position)
        self._fill(cbuf, size)
        return 1


class _buffer_writer:
    
    def __init__(self, buffer):
        self.buffer = buffer
    
    def __call__(self, _, data, size):
        block = ctypes.cast(data, ctypes.POINTER(ctypes.c_ubyte * size))
        self.buffer.write(block.contents)
        return 1


def get_bufreader(buffer):
    
    buffer.seek(0, os.SEEK_END)
    file_len = buffer.tell()
    buffer.seek(0)
    
    reader = pdfium_c.FPDF_FILEACCESS()
    reader.m_FileLen = file_len
    set_callback(reader, "m_GetBlock", _buffer_reader(buffer))
    reader.m_Param = None
    
    to_hold = (reader.m_GetBlock, )
    
    return reader, to_hold


def get_bufwriter(buffer):
    writer = pdfium_c.FPDF_FILEWRITE(version=1)
    set_callback(writer, "WriteBlock", _buffer_writer(buffer))
    return writer


def pages_c_array(pages):
    if not pages:
        return None, 0
    count = len(pages)
    c_array = (pdfium_c.FPDF_PAGE * count)(*[p.raw for p in pages])
    return c_array, count
