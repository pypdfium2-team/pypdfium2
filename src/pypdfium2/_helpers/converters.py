# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pypdfium2._helpers._utils import UnreverseBitmapStr

try:
    import PIL.Image
except ImportError:
    PIL = None

try:
    import numpy.ctypeslib
except ImportError:
    numpy = None


def to_any(result, render_kws, converter):
    c_array, *info = result
    return converter(c_array), *info


def to_numpy_ndarray(result, render_kws):
    
    if numpy is None:
        raise RuntimeError("NumPy library needs to be installed for render_tonumpy().")
    
    c_array, cl_format, (width, height) = result
    np_array = numpy.ctypeslib.as_array(c_array)
    np_array.shape = (height, width, len(cl_format))
    
    return np_array, cl_format


def to_pil_image(result, render_kws):
    
    if PIL is None:
        raise RuntimeError("Pillow library needs to be installed for render_topil().")
    
    c_array, cl_src, size = result
    cl_dst = cl_src
    if cl_src in UnreverseBitmapStr.keys():
        cl_dst = UnreverseBitmapStr[cl_src]
    
    return PIL.Image.frombuffer(cl_dst, size, c_array, "raw", cl_src, 0, 1)


class BitmapConv:
    
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs


class BitmapConvAliases:
    
    # deprecated aliases, retained for backwards compatibility
    
    def render_to(self):
        raise NotImplementedError("Inheriting class must implement `render_to()`.")
    
    def render_tobytes(self, **kwargs):
        return self.render_to(BitmapConv(to_any, bytes), **kwargs)
    
    def render_tonumpy(self, **kwargs):
        return self.render_to(BitmapConv(to_numpy_ndarray), **kwargs)
    
    def render_topil(self, **kwargs):
        return self.render_to(BitmapConv(to_pil_image), **kwargs)
