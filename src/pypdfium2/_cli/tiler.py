# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import ctypes
import os.path
from enum import Enum
from pypdfium2 import _namespace as pdfium
from pypdfium2._cli._parser import ArgParser


class Units (Enum):
    PT = 0
    MM = 1
    CM = 2
    IN = 3


def units_to_pt(value, unit: Units):
    if unit is Units.PT:
        return value
    elif unit is Units.IN:
        return value*72
    elif unit is Units.CM:
        return (value*72) / 2.54
    elif unit is Units.MM:
        return (value*72) / 25.4
    else:
        raise ValueError("Invalid unit type {}".format(unit))


def parse_args(argv, prog, desc):
    
    parser = ArgParser(
        prog = prog,
        description = desc,
    )
    parser.add_argument(
        'input',
        help = "PDF file on which to perform N-up compositing",
    )
    parser.add_argument(
        '--output', '-o',
        type = os.path.abspath,
        help = "Target path for the new document",
    )
    parser.add_argument(
        '--rows', '-r',
        type = int,
        required = True,
        help = "Number of rows (horizontal tiles)",
    )
    parser.add_argument(
        '--cols', '-c',
        type = int,
        required = True,
        help = "Number of columns (vertical tiles)",
    )
    parser.add_argument(
        '--width',
        type = float,
        required = True,
        help = "Target width",
    )
    parser.add_argument(
        '--height',
        type = float,
        required = True,
        help = "Target height",
    )
    parser.add_argument(
        '--unit', '-u',
        default = Units.MM,
        type = lambda string: Units[string.upper()],
        help = "Unit for target width and height (pt, mm, cm, in)",
    )
    
    return parser.parse_args(argv)
    


def main(argv, prog, desc):
    
    args = parse_args(argv, prog, desc)
    
    width = units_to_pt(args.width, args.unit)
    height = units_to_pt(args.height, args.unit)
    
    with pdfium.PdfContext(args.input) as src_pdf:
        
        dest_pdf = pdfium.FPDF_ImportNPagesToOne(
            src_pdf,
            ctypes.c_float(width),       # output_width
            ctypes.c_float(height),      # output_height
            ctypes.c_size_t(args.cols),  # num_pages_on_x_axis
            ctypes.c_size_t(args.rows),  # num_pages_on_y_axis
        )
        
        with open(args.output, 'wb') as file_handle:
            pdfium.save_pdf(dest_pdf, file_handle)
        
        pdfium.close_pdf(dest_pdf)
