# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers.constants import ViewMode


def translate_viewmode(viewmode):
    """
    Convert a PDFium view mode integer to an attribute of the :class:`.ViewMode` enum.
    
    Parameters:
        viewmode (int): PDFium view mode integer.
    
    Returns:
        :class:`.ViewMode`
    """
    
    if viewmode == pdfium.PDFDEST_VIEW_UNKNOWN_MODE:
        return ViewMode.Unknown
    elif viewmode == pdfium.PDFDEST_VIEW_XYZ:
        return ViewMode.XYZ
    elif viewmode == pdfium.PDFDEST_VIEW_FIT:
        return ViewMode.Fit
    elif viewmode == pdfium.PDFDEST_VIEW_FITH:
        return ViewMode.FitH
    elif viewmode == pdfium.PDFDEST_VIEW_FITV:
        return ViewMode.FitV
    elif viewmode == pdfium.PDFDEST_VIEW_FITR:
        return ViewMode.FitR
    elif viewmode == pdfium.PDFDEST_VIEW_FITB:
        return ViewMode.FitB
    elif viewmode == pdfium.PDFDEST_VIEW_FITBH:
        return ViewMode.FitBH
    elif viewmode == pdfium.PDFDEST_VIEW_FITBV:
        return ViewMode.FitBV
    else:
        raise ValueError("Unknown PDFium viewmode value {}".format(viewmode))


def translate_rotation(rotation):
    """
    Convert a rotation value in degrees to a PDFium rotation constant.
    
    Parameters:
        rotation (int): Rotation value in degrees (0, 90, 180, 270).
    
    Returns:
        :class:`int` – A PDFium rotation constant (0, 1, 2, 3).
    """
    
    if rotation == 0:
        return 0
    elif rotation == 90:
        return 1
    elif rotation == 180:
        return 2
    elif rotation == 270:
        return 3
    else:
        raise ValueError("Invalid rotation {}".format(rotation))


def _hex_digits(c):
    
    hxc = hex(c)[2:]
    if len(hxc) == 1:
        hxc = "0" + hxc
    
    return hxc
    

def colour_as_hex(r, g, b, a=255):
    """
    Convert a colour given as values of red, green, blue, and alpha ranging from 0 to 255 to a single integer in 32-bit ARGB format.
    
    Returns:
        :class:`int`, :class:`bool` – The colour integer, and a logical value that is :data:`True` if an alpha channel is needed, or :data:`False` if it is not needed.
    """
    
    use_alpha = True
    if a == 255:
        use_alpha = False
    
    colours = (a, r, g, b)
    for c in colours:
        assert 0 <= c <= 255
    
    hxc_str = "0x"
    for c in colours:
        hxc_str += _hex_digits(c)
    
    hxc_int = int(hxc_str, 0)
    
    return hxc_int, use_alpha
