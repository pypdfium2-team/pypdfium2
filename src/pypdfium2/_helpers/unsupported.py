# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ("PdfUnspHandler", )

import atexit
import logging
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i
from pypdfium2._helpers.misc import PdfiumError

lib_logger = logging.getLogger("pypdfium2")


class PdfUnspHandler (pdfium_i.AutoCastable):
    """
    Unsupported feature handler helper class.
    
    Attributes:
        raw (UNSUPPORT_INFO):
           The underlying pdfium ``UNSUPPORT_INFO`` struct.
        handlers (dict[str, typing.Callable]):
            A dictionary of named handler functions to be called with an unsupported code (:attr:`FPDF_UNSP_*`) when PDFium detects an unsupported feature.
    """
    
    SINGLETON = None
    
    def __init__(self):
        self.handlers = {}
        self.raw = pdfium_c.UNSUPPORT_INFO(version=1)
    
    def __call__(self, _, type):
        for handler in self.handlers.values():
            handler(type)
    
    @staticmethod
    def _default(type):
        lib_logger.warning(f"Unsupported PDF feature: {pdfium_i.UnsupportedInfoToStr.get(type)}")
    
    def _keep(self):
        id(self.handlers)
        id(self.raw)
    
    def setup(self, add_default=True):
        """
        Register the handler with PDFium, and install an exit function that will keep the object alive until the end of session.
        
        Once set up, a :class:`.PdfUnspHandler` cannot be removed. It stands and falls with the library.
        Thus, this function can only be called once in a session.
        However, you may change the wrapped :attr:`.handlers` callbacks.
        Call ``.handlers.clear()`` to remove all handlers, thereby effectively disabling the instance.
        
        Parameters:
            add_default (bool):
                If True, add a default callback that will log unsupported features as warning.
        """
        if PdfUnspHandler.SINGLETON:
            raise RuntimeError("Only one PdfUnspHandler instance can be registered for a session.")
        
        pdfium_i.set_callback(self.raw, "FSDK_UnSupport_Handler", self)
        ok = pdfium_c.FSDK_SetUnSpObjProcessHandler(self.raw)
        if not ok:
            raise PdfiumError("Failed to register PdfUnspHandler object.")
        PdfUnspHandler.SINGLETON = self
        
        # TODO might want to have this unregistered in destroy_lib() after library destruction
        atexit.register(self._keep)
        if add_default:
            self.handlers["default"] = PdfUnspHandler._default
