# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os.path
from enum import Enum
from pypdfium2 import _namespace as pdfium


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


def attach_parser(subparsers):
    parser = subparsers.add_parser(
        "tile",
        help = "Perform page tiling (N-up compositing)",
    )
    parser.add_argument(
        "input",
        help = "PDF file on which to perform N-up compositing",
    )
    parser.add_argument(
        "--password",
        help = "Password to unlock the PDF, if encrypted"
    )
    parser.add_argument(
        "--output", "-o",
        required = True,
        type = os.path.abspath,
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
    
    width = units_to_pt(args.width, args.unit)
    height = units_to_pt(args.height, args.unit)
    
    src_pdf = pdfium.PdfDocument(args.input, password=args.password)
    raw_dest = pdfium.FPDF_ImportNPagesToOne(
        src_pdf.raw,
        width, height,
        args.cols, args.rows,
    )
    dest_pdf = pdfium.PdfDocument(raw_dest)
    with open(args.output, "wb") as buffer:
        dest_pdf.save(buffer)
