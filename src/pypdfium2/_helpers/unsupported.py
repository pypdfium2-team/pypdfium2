# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ["PdfUnspHandler"]

import atexit
import logging
import pypdfium2.raw as pdfium_c
from pypdfium2._helpers._internal import consts, utils

lib_logger = logging.getLogger("pypdfium2")


class PdfUnspHandler:
    """
    Unsupported feature handler helper class.
    
    Attributes:
        handlers (dict[str, typing.Callable]):
            A dictionary of named handler functions to be called with an unsupported code (:attr:`FPDF_UNSP_*`) when PDFium detects an unsupported feature.
    """
    
    def __init__(self):
        self.handlers = {}
    
    def __call__(self, _, type):
        for handler in self.handlers.values():
            handler(type)
    
    
    def setup(self, add_default=True):
        """
        Attach the handler to PDFium, and register an exit function to keep the object alive for the rest of the session.
        
        Parameters:
            add_default (bool):
                If True, add a default callback that will log unsupported features as warning.
        """
        
        self._config = pdfium_c.UNSUPPORT_INFO(version=1)
        utils.set_callback(self._config, "FSDK_UnSupport_Handler", self)
        pdfium_c.FSDK_SetUnSpObjProcessHandler(self._config)
        
        atexit.register(self._keep)
        
        if add_default:
            self.handlers["default"] = PdfUnspHandler._default
    
    
    def _keep(self):
        id(self.handlers)
        id(self._config)
    
    
    @staticmethod
    def _default(type):
        # skip codes of features that pdfium now supports but still erroneously claims unsupported (https://crbug.com/pdfium/1945)
        if type in (pdfium_c.FPDF_UNSP_DOC_ATTACHMENT, ):
            return
        lib_logger.warning("Unsupported PDF feature: %s" % consts.UnsupportedInfoToStr.get(type))
