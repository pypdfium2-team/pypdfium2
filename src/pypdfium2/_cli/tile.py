# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from enum import Enum
from pathlib import Path
import pypdfium2.raw as pdfium_c
import pypdfium2._helpers as pdfium
from pypdfium2._cli._parsers import add_input, get_input


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
        raise ValueError("Invalid unit type %s" % unit)


def attach(parser):
    add_input(parser, pages=False)
    parser.add_argument(
        "--output", "-o",
        required = True,
        type = Path,
        help = "Target path for the new document",
    )
    parser.add_argument(
        "--rows", "-r",
        type = int,
        required = True,
        help = "Number of rows (horizontal tiles)",
    )
    parser.add_argument(
        "--cols", "-c",
        type = int,
        required = True,
        help = "Number of columns (vertical tiles)",
    )
    parser.add_argument(
        "--width",
        type = float,
        required = True,
        help = "Target width",
    )
    parser.add_argument(
        "--height",
        type = float,
        required = True,
        help = "Target height",
    )
    parser.add_argument(
        "--unit", "-u",
        default = Units.MM,
        type = lambda string: Units[string.upper()],
        help = "Unit for target width and height (pt, mm, cm, in)",
    )    


def main(args):
    
    # Rudimentary page tiling, powered by pdfium
    # Could also implement a custom, more sophisticated page tiler via XObject placement
    
    width = units_to_pt(args.width, args.unit)
    height = units_to_pt(args.height, args.unit)
    
    src_pdf = get_input(args)
    raw_dest = pdfium_c.FPDF_ImportNPagesToOne(
        src_pdf.raw,
        width, height,
        args.cols, args.rows,
    )
    dest_pdf = pdfium.PdfDocument(raw_dest)
    dest_pdf.save(args.output)
