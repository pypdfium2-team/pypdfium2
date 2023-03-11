# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from pathlib import Path
import pypdfium2._helpers as pdfium


def parse_numtext(numtext):
    
    # TODO enhancement: take count and verify page numbers
    
    if not numtext:
        return None
    indices = []
    
    for num_or_range in numtext.split(","):
        if "-" in num_or_range:
            start, end = num_or_range.split("-")
            start = int(start) - 1
            end   = int(end)   - 1
            if start < end:
                indices.extend( [i for i in range(start, end+1)] )
            else:
                indices.extend( [i for i in range(start, end-1, -1)] )
        else:
            indices.append(int(num_or_range) - 1)
    
    return indices


def round_list(lst, n_digits):
    if not lst:
        return lst
    result = [round(v, n_digits) for v in lst]
    if isinstance(lst, tuple):
        result = tuple(result)
    return result


def add_input(parser, pages=True):
    # TODO add option to open file with buffer/bytes strategy
    parser.add_argument(
        "input",
        type = Path,
        help = "Input PDF document",
    )
    parser.add_argument(
        "--password",
        help = "A password to unlock the PDF, if encrypted",
    )
    if pages:
        parser.add_argument(
            "--pages",
            default = None,
            type = parse_numtext,
            help = "Page numbers and ranges to include",
        )


def add_n_digits(parser):
    parser.add_argument(
        "--n-digits",
        type = int,
        default = 4,
        help = "Number of digits to which coordinates/sizes shall be rounded",
    )


def get_input(args, **kwargs):
    pdf = pdfium.PdfDocument(args.input, password=args.password, **kwargs)
    if "pages" in args and not args.pages:
        args.pages = [i for i in range(len(pdf))]
    return pdf
