# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from enum import Enum


class OptimiseMode (Enum):
    """ How to optimise page rendering """
    none = 0          #: Do not use any optimisations
    lcd_display = 1   #: Optimise for LCD displays
    printing = 2      #: Optimise for printing


class ViewMode (Enum):
    """ Modes that define how target coordinates of bookmarks should be interpreted. """
    Unknown = 0
    XYZ     = 1
    Fit     = 2
    FitH    = 3
    FitV    = 4
    FitR    = 5
    FitB    = 6
    FitBH   = 7
    FitBV   = 8
