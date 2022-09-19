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


def bitmap_conv(main_func):
    def factory_func(*conv_args, **conv_kws):
        def actual_func(result, renderer_kws):
            return main_func(result, renderer_kws, *conv_args, **conv_kws)
        return actual_func
    return factory_func


class BitmapConv:
    
    @bitmap_conv
    @staticmethod
    def any(result, renderer_kws, converter):
        c_array, *info = result
        return converter(c_array), *info
    
    @bitmap_conv
    @staticmethod
    def numpy_ndarray(result, renderer_kws):
        
        if numpy is None:
            raise RuntimeError("NumPy library needs to be installed for render_tonumpy().")
        
        c_array, cl_format, (width, height) = result
        np_array = numpy.ctypeslib.as_array(c_array)
        np_array.shape = (height, width, len(cl_format))
        
        return np_array, cl_format
    
    @bitmap_conv
    @staticmethod
    def pil_image(result, renderer_kws):
        
        if PIL is None:
            raise RuntimeError("Pillow library needs to be installed for render_topil().")
        
        c_array, cl_src, size = result
        cl_dst = cl_src
        if cl_src in UnreverseBitmapStr.keys():
            cl_dst = UnreverseBitmapStr[cl_src]
        
        return PIL.Image.frombuffer(cl_dst, size, c_array, "raw", cl_src, 0, 1)
