# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
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


def add_input(parser, pages=True):
    parser.add_argument(
        "input",
        type = Path,
        help = "Input PDF document",
    )
    parser.add_argument(
        "--password",
        help = "A password to unlock the PDF, if encrypted",
    )
    parser.add_argument(
        # TODO choices
        "--opener",
        help = "File access strategy to use",
        type = lambda s: pdfium.FileAccessMode[s.upper()],
        default = pdfium.FileAccessMode.NATIVE,
    )
    if pages:
        parser.add_argument(
            "--pages",
            default = None,
            type = parse_numtext,
            help = "Page numbers and ranges to include",
        )


def get_input(args):
    pdf = pdfium.PdfDocument(args.input, password=args.password, file_access=args.opener)
    if "pages" in args and not args.pages:
        args.pages = [i for i in range(len(pdf))]
    return pdf
