# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import copy
import ctypes
import pypdfium2.raw as pdfium_c
from pypdfium2._helpers._internal import consts


def color_tohex(color, rev_byteorder):
    
    if len(color) != 4:
        raise ValueError("Color must consist of exactly 4 values.")
    if not all(0 <= c <= 255 for c in color):
        raise ValueError("Color value exceeds boundaries.")
    
    r, g, b, a = color
    
    # color is interpreted differently with FPDF_REVERSE_BYTE_ORDER (perhaps inadvertently?)
    if rev_byteorder:
        channels = (a, b, g, r)
    else:
        channels = (a, r, g, b)
    
    c_color = 0
    shift = 24
    for c in channels:
        c_color |= c << shift
        shift -= 8
    
    return c_color


def get_functype(struct, funcname):
    return {k: v for k, v in struct._fields_}[funcname]


def get_struct_slots(struct):
    return copy.copy(struct.__slots__)


def image_metadata_to_str(metadata, pad=""):
    imageinfo_maps = {"colorspace": consts.ColorspaceToStr}
    as_str = ""
    nl = ""
    for attr in get_struct_slots(pdfium_c.FPDF_IMAGEOBJ_METADATA):
        value = getattr(metadata, attr)
        if attr in imageinfo_maps:
            value = imageinfo_maps[attr].get(value, "PDFium constant %s" % value)
        as_str += nl + pad + "%s: %s" % (attr, value)
        nl = "\n"
    return as_str


def is_buffer(buf, spec="r"):
    methods = []
    if "r" in spec:
        methods += ["seek", "tell", "read", "readinto"]
    if "w" in spec:
        methods += ["write"]
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
    
    buffer.seek(0, 2)
    file_len = buffer.tell()
    buffer.seek(0)
    
    reader = pdfium_c.FPDF_FILEACCESS()
    reader.m_FileLen = file_len
    reader.m_GetBlock = get_functype(pdfium_c.FPDF_FILEACCESS, "m_GetBlock")( _buffer_reader(buffer) )
    reader.m_Param = None
    
    to_hold = (reader.m_GetBlock, buffer)
    
    return reader, to_hold


def get_bufwriter(buffer):
    writer = pdfium_c.FPDF_FILEWRITE()
    writer.version = 1
    writer.WriteBlock = get_functype(pdfium_c.FPDF_FILEWRITE, "WriteBlock")( _buffer_writer(buffer) )
    return writer


def get_pause_struct(func):
    pause = pdfium_c.IFSDK_PAUSE()
    pause.version = 1
    pause.NeedToPauseNow = get_functype(pdfium_c.IFSDK_PAUSE, "NeedToPauseNow")(func)
    return pause


def pages_c_array(pages):
    if not pages:
        return None, 0
    count = len(pages)
    c_array = (pdfium_c.FPDF_PAGE * count)(*[p.raw for p in pages])
    return c_array, count
