# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

__all__ = ["PdfAttachment"]

import ctypes
import pypdfium2.raw as pdfium_c
from pypdfium2._helpers.misc import PdfiumError


def _encode_key(key):
    if isinstance(key, str):
        return (key + "\x00").encode("utf-8")
    else:
        raise TypeError("Key must be str, but %s was given." % type(key).__name__)


class PdfAttachment:
    """
    Attachment helper class.
    See PDF 1.7, Section 7.11 "File Specifications".
    
    Attributes:
        raw (FPDF_ATTACHMENT):
            The underlying PDFium attachment handle.
        pdf (PdfDocument):
            Reference to the document this attachment belongs to. Must remain valid as long as the attachment is used.
    """
    
    # Problems with PDFium's attachment API:
    # - https://crbug.com/pdfium/1939
    # - https://crbug.com/pdfium/893
    
    
    def __init__(self, raw, pdf):
        # assuming an (unused) reference is enough to keep the parent pdf alive
        self.raw = raw
        self.pdf = pdf
    
    
    def get_name(self):
        """
        Returns:
            str: Name of the attachment.
        """
        n_bytes = pdfium_c.FPDFAttachment_GetName(self.raw, None, 0)
        buffer = ctypes.create_string_buffer(n_bytes)
        buffer_ptr = ctypes.cast(buffer, ctypes.POINTER(pdfium_c.FPDF_WCHAR))
        pdfium_c.FPDFAttachment_GetName(self.raw, buffer_ptr, n_bytes)
        return buffer.raw[:n_bytes-2].decode("utf-16-le")
    
    
    def get_data(self):
        """
        Returns:
            ctypes.Array: The attachment's file data (as :class:`ctypes.c_char` array).
        """
                
        n_bytes = ctypes.c_ulong()
        pdfium_c.FPDFAttachment_GetFile(self.raw, None, 0, n_bytes)
        n_bytes = n_bytes.value
        if n_bytes == 0:
            raise PdfiumError("Failed to extract attachment (buffer length %s)." % (n_bytes, ))
        
        buffer = ctypes.create_string_buffer(n_bytes)
        out_buflen = ctypes.c_ulong()
        success = pdfium_c.FPDFAttachment_GetFile(self.raw, buffer, n_bytes, out_buflen)
        out_buflen = out_buflen.value
        if not success:
            raise PdfiumError("Failed to extract attachment (error status).")
        if n_bytes < out_buflen:
            raise PdfiumError("Failed to extract attachment (expected %s bytes, but got %s)." % (n_bytes, out_buflen))
        
        return buffer
    
    
    def set_data(self, data):
        """
        Set the attachment's file data.
        If this function is called on an existing attachment, it will be changed to point at the new data,
        but the previous data will not be removed from the file (as of PDFium 5418).
        
        Parameters:
            data (bytes | ctypes.Array):
                New file data for the attachment. May be any data type that can be implicitly converted to :class:`ctypes.c_void_p`.
        """
        success = pdfium_c.FPDFAttachment_SetFile(self.raw, self.pdf.raw, data, len(data))
        if not success:
            raise PdfiumError("Failed to set attachment data.")
    
    
    def has_key(self, key):
        """
        Parameters:
            key (str):
                A key to look for in the attachment's params dictionary.
        Returns:
            bool: True if *key* is contained in the params dictionary, False otherwise.
        """
        return pdfium_c.FPDFAttachment_HasKey(self.raw, _encode_key(key))
    
    
    def get_value_type(self, key):
        """
        Returns:
            int: Type of the value of *key* in the params dictionary (:attr:`FPDF_OBJECT_*`).
        """
        return pdfium_c.FPDFAttachment_GetValueType(self.raw, _encode_key(key))
    
    
    def get_str_value(self, key):
        """
        Returns:
            str: The value of *key* in the params dictionary, if it is a string or name.
            Otherwise, an empty string will be returned. On other failures, an exception will be raised.
        """
        
        enc_key = _encode_key(key)
        n_bytes = pdfium_c.FPDFAttachment_GetStringValue(self.raw, enc_key, None, 0)
        if n_bytes <= 0:
            raise PdfiumError("Failed to get value of key '%s'." % (key, ))
        
        buffer = ctypes.create_string_buffer(n_bytes)
        buffer_ptr = ctypes.cast(buffer, ctypes.POINTER(pdfium_c.FPDF_WCHAR))
        pdfium_c.FPDFAttachment_GetStringValue(self.raw, enc_key, buffer_ptr, n_bytes)
        
        return buffer.raw[:n_bytes-2].decode("utf-16-le")
    
    
    def set_str_value(self, key, value):
        """
        Set the attribute specified by *key* to the string *value*.
        
        Parameters:
            value (str): New string value for the attribute.
        """
        enc_value = (value + "\x00").encode("utf-16-le")
        enc_value_ptr = ctypes.cast(enc_value, pdfium_c.FPDF_WIDESTRING)
        success = pdfium_c.FPDFAttachment_SetStringValue(self.raw, _encode_key(key), enc_value_ptr)
        if not success:
            raise PdfiumError("Failed to set attachment param '%s' to '%s'." % (key, value))
