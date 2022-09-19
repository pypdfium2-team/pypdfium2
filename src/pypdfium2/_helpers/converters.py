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
    """
    Parent class for bitmap converters compatible with :meth:`.PdfPage.render_to` / :meth:`.PdfDocument.render_to`.
    The constructor captures any arguments (positionals and keywords) and adds them to the :meth:`.run` call.
    It is not necessary to implement a constructor in the inheriting class.
    
    Tip:
        If you wish to implement a custom converter that does not take any parametrs, note that ``render_to()`` accepts any callable.
        It does not necessarily have to be an instance of this class.
    """
    
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    
    @staticmethod
    def run(result, renderer_kws, *args, **kwargs):  # generic header
        """
        The actual converter function, to be implemented by the inheriting class.
        See below for a specification of the parameters that will be passed to the function.
        
        Parameters:
            result (tuple):
                Result of the :meth:`.PdfPage.render_base` call (ctypes ubyte array, color format, size).
            renderer_kws (dict):
                Dictionary of keywords that were passed to :meth:`.PdfPage.render_base` by the caller. May be empty.
            args (tuple):
                Further positional arguments captured by the constructor.
                The overriding function may take custom parameters, but must not capture arbitrary arguments!
            kwargs (dict):
                Further keyword arguments captured by the constructor.
                The overriding function may take custom parameters, but must not capture arbitrary keywords!
        Returns:
            typing.Any:
                The converted rendering result (implementation-specific).
                If the converter is used with :meth:`.PdfDocument.render_to` (or anything else that uses :mod:`multiprocessing`),
                the return values must be compatible with :mod:`pickle`.
        """
        raise NotImplementedError("Inheriting class must provide run() method.")


class BitmapConv:
    
    class any (BitmapConvBase):
        """
        Simple factory for converters that merely translate the ctypes array, while passing through additional information unaffected.
        
        Example:
            ``render_to(BitmapConv.any(bytes), **kwargs)``:
                Get the pixel data as bytes (independent copy of the ctypes array).
        
        Parameters:
            converter (typing.Callable):
                A callable to translate a ctypes array to a different data type.
                The callable could be a function, a class with constructor, or an instance of a class implementing ``__call__(self, ...)``.
        Returns:
            (typing.Any, ...):
                The converted rendering result (implementation-specific), and additional information returned by :meth:`.PdfPage.render_base` (color format, size).
        """
        
        @staticmethod
        def run(result, renderer_kws, converter):
            c_array, *info = result
            return converter(c_array), *info
    
    class numpy_ndarray (BitmapConvBase):
        """
        *Requires* :mod:`numpy`.
        
        Get the bitmap as shaped NumPy array referencing the original ctypes array.
        This converter never makes a copy of the data.
        
        Returns:
            (numpy.ndarray, str): NumPy array, and color format.
        
        Note:
            This converter does not return bitmap size because the array is multi-dimensional,
            so this information is already contained in the array's shape.
        """
        
        @staticmethod
        def run(result, renderer_kws):
            
            if numpy is None:
                raise RuntimeError("NumPy library needs to be installed for numpy_ndarray() converter.")
            
            c_array, cl_format, (width, height) = result
            np_array = numpy.ctypeslib.as_array(c_array)
            np_array.shape = (height, width, len(cl_format))
            
            return np_array, cl_format
    
    class pil_image (BitmapConvBase):
        """
        *Requires* :mod:`PIL`.
        
        Get the bitmap as PIL image.
        
        Parameters:
            prefer_la (bool):
                If :data:`True`, automatically convert ``RGBA``/``BGRA`` to ``LA`` if rendering in greyscale mode with alpha channel
                (PDFium does not provide ``LA`` output directly).
        Returns:
            PIL.Image.Image: The image object.
        
        Note:
            This converter does not return additional parameters.
            Information on size and color format (mode) is already contained in the image object.
        Hint:
            This uses :func:`PIL.Image.frombuffer` under the hood.
            If possible for the color format in question, the image will reference the ctypes array. Otherwise, PIL may create a copy of the data.
            At the time of writing, PIL can directly work with ``RGBA``, ``RGBX`` or ``L`` pixel data (see :attr:`PIL.Image._MAPMODES`).
            Depending on the use case, you may want to consider setting the rendering parameters *rev_byteorder* and *prefer_bgrx* to :data:`True`
            to generate natively compatible output.
        """
        
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
    """
    Base class for deprecated rendering target aliases.
    Retained for backwards compatibility, but might be removed in the future.
    The :meth:`.PdfPage.render_to` / :meth:`.PdfDocument.render_to` APIs should be used instead.
    """
    
    def render_to(self):
        """
        Method to be implemented by the inheriting class.
        """
        raise NotImplementedError("Inheriting class must provide render_to() method.")
    
    def render_tobytes(self, **kwargs):
        """
        .. deprecated:: 3.0
            Use ``render_to(BitmapConv.any(bytes), **kwargs)`` instead. See :class:`.BitmapConv.any`.
        Note:
            This creates an independent copy of the pixel data, which should be avoided in general.
        """
        return self.render_to(BitmapConv.any(bytes), **kwargs)
    
    def render_tonumpy(self, **kwargs):
        """
        .. deprecated:: 3.0
            Use ``render_to(BitmapConv.numpy_ndarray, **kwargs)`` instead. See :class:`.BitmapConv.numpy_ndarray`.
        """
        return self.render_to(BitmapConv.numpy_ndarray, **kwargs)
    
    def render_topil(self, prefer_la=False, **kwargs):
        """
        .. deprecated:: 3.0
            Use ``render_to(BitmapConv.pil_image, **kwargs)`` instead. See :class:`.BitmapConv.pil_image`.
        """
        return self.render_to(BitmapConv.pil_image(prefer_la=prefer_la), **kwargs)
