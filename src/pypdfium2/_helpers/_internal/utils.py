# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
import pypdfium2.raw as pdfium_c


def color_tohex(color, rev_byteorder):
    """
    Convert an RGBA color tuple to a single hex value (ARGB or ABGR).
    
    Parameters:
        color (tuple[int, int, int, int]):
        rev_byteorder (bool):
            If False, produce ARGB output.
            If True, produce ABGR output for use with FPDF_REVERSE_BYTE_ORDER.
    Returns:
        int: Hex color value.
    """
    
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
    """
    Set a callback function on a struct.
    This automates wrapping the callback in the corresponding CFUNCTYPE.
    
    struct (ctypes.Structure):
        The struct object.
    fname (str):
        Name of the target field for the callback.
    callback (typing.Callable):
        The callback function to assign to the field.
    """
    setattr(struct, fname, type(getattr(struct, fname))(callback))


def is_buffer(buf, spec="r"):
    methods = ()
    if "r" in spec:
        methods += ("seek", "tell", "read", "readinto")
    if "w" in spec:
        methods += ("write", )
    return all(callable(getattr(buf, a, None)) for a in methods)


class _buffer_reader:
    
    def __init__(self, buffer):
        self.buffer = buffer
    
    def __call__(self, _, position, p_buf, size):
        c_buf = ctypes.cast(p_buf, ctypes.POINTER(ctypes.c_char * size))
        self.buffer.seek(position)
        self.buffer.readinto(c_buf.contents)
        return 1


class _buffer_writer:
    
    def __init__(self, buffer):
        self.buffer = buffer
    
    def __call__(self, _, data, size):
        block = ctypes.cast(data, ctypes.POINTER(ctypes.c_ubyte * size))
        self.buffer.write(block.contents)
        return 1


def get_bufreader(buffer):
    """
    Returns:
        (FPDF_FILEACCESS, tuple): PDFium interface struct wrapping the given readable buffer,
        and a tuple of objects to keep alive while the buffer callback is used (as the struct object itself may be discarded earlier).
    """
    
    buffer.seek(0, 2)
    file_len = buffer.tell()
    buffer.seek(0)
    
    reader = pdfium_c.FPDF_FILEACCESS()
    reader.m_FileLen = file_len
    set_callback(reader, "m_GetBlock", _buffer_reader(buffer))
    reader.m_Param = None
    
    to_hold = (reader.m_GetBlock, buffer)
    
    return reader, to_hold


def get_bufwriter(buffer):
    """
    Returns:
        FPDF_FILEWRITE: PDFium interface struct wrapping the given writeable buffer.
    """
    writer = pdfium_c.FPDF_FILEWRITE(version=1)
    set_callback(writer, "WriteBlock", _buffer_writer(buffer))
    return writer


def pages_c_array(pages):
    if not pages:
        return None, 0
    count = len(pages)
    c_array = (pdfium_c.FPDF_PAGE * count)(*[p.raw for p in pages])
    return c_array, count
