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


class BitmapConvBase:
    
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    
    @staticmethod
    def run():
        raise NotImplementedError("Inheriting class must provide run() method.")


class BitmapConv:
    
    class any (BitmapConvBase):
        
        @staticmethod
        def run(result, renderer_kws, converter):
            c_array, *info = result
            return converter(c_array), *info
    
    class numpy_ndarray (BitmapConvBase):
        
        @staticmethod
        def run(result, renderer_kws):
            
            if numpy is None:
                raise RuntimeError("NumPy library needs to be installed for numpy_ndarray() converter.")
            
            c_array, cl_format, (width, height) = result
            np_array = numpy.ctypeslib.as_array(c_array)
            np_array.shape = (height, width, len(cl_format))
            
            return np_array, cl_format
    
    class pil_image (BitmapConvBase):
        
        @staticmethod
        def run(result, renderer_kws, prefer_la=False):
            
            if PIL is None:
                raise RuntimeError("Pillow library needs to be installed for pil_image() converter.")
            
            c_array, cl_src, size = result
            cl_dst = cl_src
            if cl_src in UnreverseBitmapStr.keys():
                cl_dst = UnreverseBitmapStr[cl_src]
            
            pil_image = PIL.Image.frombuffer(cl_dst, size, c_array, "raw", cl_src, 0, 1)
            if prefer_la:
                if renderer_kws.get("greyscale", False) and cl_dst == "RGBA":
                    pil_image = pil_image.convert("LA")
            
            return pil_image


class BitmapConvAliases:
    
    # deprecated aliases, retained for backwards compatibility
    
    def render_to(self):
        raise NotImplementedError("Inheriting class must provide render_to() method.")
    
    def render_tobytes(self, **kwargs):
        return self.render_to(BitmapConv.any(bytes), **kwargs)
    
    def render_tonumpy(self, **kwargs):
        return self.render_to(BitmapConv.numpy_ndarray, **kwargs)
    
    def render_topil(self, prefer_la=False, **kwargs):
        return self.render_to(BitmapConv.pil_image(prefer_la=prefer_la), **kwargs)
