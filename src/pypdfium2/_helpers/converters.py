# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pypdfium2._helpers.misc import BitmapStrReverseToRegular

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
    """
    
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    
    @staticmethod
    def run(result, renderer_kws, *args, **kwargs):
        """
        The actual converter function, to be implemented by the inheriting class.
        The header reflects what the function may receive (two mandatory positionals, and arbitrary implementation-dependent parameters).
        See below for a specification.
        
        Note:
            * :meth:`.run` should be implemented as a :func:`staticmethod`.
            * If the implementation takes additional parameters, it is expected to define them on an explicit basis.
              Unrecognised arguments should always be refused.
        
        Parameters:
            result (tuple):
                Result of the :meth:`.PdfPage.render_base` call (ctypes array, colour format, size).
            renderer_kws (dict):
                Dictionary of keywords that were passed to :meth:`.PdfPage.render_base` by the caller. May be empty.
            args (tuple):
                Further positional arguments to the converter, as captured by the constructor (see note above).
            kwargs (dict):
                Further keyword arguments to the converter, as captured by the constructor (see note above).
        Returns:
            typing.Any: The converted rendering result (implementation-specific).
        """
        raise NotImplementedError("Inheriting class must provide run() method.")


class BitmapConv:
    """
    Built-in converters to be applied on the rendering result.
    """
    
    # Technically, the converter implementations are standalone - the outer class is just to nicely enclose them in one namespace.
    
    class any (BitmapConvBase):
        """
        Simple factory for converters that merely work with the ctypes array, while passing through additional information unaffected.
        
        Example:
            ``render_to(BitmapConv.any(bytes), **kwargs)``:
                Get the pixel data as bytes. (Note, though, that this would create an independent copy of the pixel data, which should be avoided in general.)
        
        Parameters:
            converter (typing.Callable):
                A callable to translate a ctypes array to a different data type.
                It could be a function, a class with constructor, or an instance of a class implementing ``__call__``.
        Returns:
            (typing.Any, str, (int, int)): The converted bitmap (implementation-specific), and additional information returned by :meth:`.PdfPage.render_base` (colour format, size).
        """
        
        @staticmethod
        def run(result, renderer_kws, converter):
            c_array, cl_format, size = result
            return converter(c_array), cl_format, size
    
    
    class numpy_ndarray (BitmapConvBase):
        """
        *Requires* :mod:`numpy`
        
        Get the bitmap as shaped NumPy array referencing the original ctypes array.
        This converter never makes a copy of the data.
        
        Returns:
            (numpy.ndarray, str): NumPy array, and colour format.
        """
        
        @staticmethod
        def run(result, renderer_kws):
            
            # NOTE This converter does not return bitmap size because the information is contained in the array's shape already.
            
            if numpy is None:
                raise RuntimeError("NumPy library needs to be installed for numpy_ndarray() converter.")
            
            c_array, cl_format, (width, height) = result
            np_array = numpy.ctypeslib.as_array(c_array)
            np_array.shape = (height, width, len(cl_format))
            
            return np_array, cl_format
    
    
    class pil_image (BitmapConvBase):
        """
        *Requires* :mod:`PIL`
        
        Get the bitmap as PIL image.
        
        Parameters:
            prefer_la (bool):
                If :data:`True`, automatically convert ``RGBA``/``BGRA`` to ``LA`` if rendering in greyscale mode with alpha channel
                (PDFium does not provide ``LA`` output directly).
        Returns:
            PIL.Image.Image: The image object.
        
        Hint:
            This uses :func:`PIL.Image.frombuffer` under the hood.
            If possible for the colour format in question, the image will reference the ctypes array. Otherwise, PIL may create a copy of the data.
            At the time of writing, PIL can directly work with ``RGBA``, ``RGBX`` or ``L`` (among the pixel formats supported by PDFium).
            Depending on the use case, you may want to consider setting the rendering parameters *rev_byteorder* and *prefer_bgrx* to :data:`True`
            to generate natively compatible output.
        """
        
        @staticmethod
        def run(result, renderer_kws, prefer_la=False):
            
            # NOTE This converter does not return additional parameters, as information on size and colour format (mode) is already contained in the image object.
            
            if PIL is None:
                raise RuntimeError("Pillow library needs to be installed for pil_image() converter.")
            
            c_array, cl_src, size = result
            cl_dst = cl_src
            if cl_src in BitmapStrReverseToRegular.keys():
                cl_dst = BitmapStrReverseToRegular[cl_src]
            
            pil_image = PIL.Image.frombuffer(cl_dst, size, c_array, "raw", cl_src, 0, 1)
            if prefer_la:
                if renderer_kws.get("greyscale", False) and cl_dst == "RGBA":
                    pil_image = pil_image.convert("LA")
            
            return pil_image


class BitmapConvAliases:
    """
    Base class containing rendering target aliases.
    Currently retained for backwards compatibility, but may be deprecated in the future.
    Consider using the :meth:`.PdfPage.render_to` / :meth:`.PdfDocument.render_to` APIs instead.
    """
    
    def render_to(self):
        """ Method to be implemented by the inheriting class. """
        raise NotImplementedError("Inheriting class must provide render_to() method.")
    
    def render_tobytes(self, **kwargs):
        """ Alias for ``render_to(BitmapConv.any(bytes), ...)``. """
        return self.render_to(BitmapConv.any(bytes), **kwargs)
    
    def render_tonumpy(self, **kwargs):
        """ Alias for ``render_to(BitmapConv.numpy_ndarray, ...)``. """
        return self.render_to(BitmapConv.numpy_ndarray, **kwargs)
    
    def render_topil(self, prefer_la=False, **kwargs):
        """ Alias for ``render_to(BitmapConv.pil_image, ...)``. """
        return self.render_to(BitmapConv.pil_image(prefer_la=prefer_la), **kwargs)
