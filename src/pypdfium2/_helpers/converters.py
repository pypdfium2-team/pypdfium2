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


class BitmapConv:
    
    @staticmethod
    def numpy_ndarray(args):
        
        if numpy is None:
            raise RuntimeError("NumPy library needs to be installed for render_tonumpy().")
        
        c_array, cl_format, (width, height) = args
        np_array = numpy.ctypeslib.as_array(c_array)
        np_array.shape = (height, width, len(cl_format))
        
        return np_array, cl_format
    
    @staticmethod
    def pil_image(args):
        
        if PIL is None:
            raise RuntimeError("Pillow library needs to be installed for render_topil().")
        
        c_array, cl_src, size = args
        cl_dst = cl_src
        if cl_src in UnreverseBitmapStr.keys():
            cl_dst = UnreverseBitmapStr[cl_src]
        
        return PIL.Image.frombuffer(cl_dst, size, c_array, "raw", cl_src, 0, 1)


class AnyBitmapConv:
    
    def __init__(self, converter):
        self.converter = converter
    
    def __call__(self, args):
        c_array, *info = args
        return self.converter(c_array), *info
