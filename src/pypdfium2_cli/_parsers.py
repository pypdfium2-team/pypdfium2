# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import argparse
from pathlib import Path
import pypdfium2._helpers as pdfium


def parse_numtext(numtext):
    
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


class _Range:
    
    def __init__(self, start, stop):
        self.start = start
        self.stop = stop
    
    def __repr__(self):
        return f"{self.start}-{self.stop}"

def pagenums_ranger(pagenums):
    
    # provided pagenums are 1-based. for 0-based, prev would have to be -2
    prev = -1
    range_start = None
    out = []
    
    for n in pagenums:
        if prev+1 == n:
            if not range_start:
                range_start = out.pop()  # prev
        else:
            if range_start:
                out.append(_Range(range_start, prev))
                range_start = None
            out.append(n)
        prev = n
    
    if range_start:
        out.append(_Range(range_start, prev))
    
    return out


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


def get_input(args, init_forms=False, **kwargs):
    pdf = pdfium.PdfDocument(args.input, password=args.password, **kwargs)
    if init_forms:
        pdf.init_forms()
    if "pages" in args and not args.pages:
        args.pages = [i for i in range(len(pdf))]
    # TODO else validate pages, as seen in ./render.py
    return pdf


# dummy more_itertools.peekable().__bool__ alternative

def _postpeek_generator(value, iterator):
    yield value; yield from iterator

def iterator_hasvalue(iterator):
    try:
        first_value = next(iterator)
    except StopIteration:
        return False, None
    else:
        return True, _postpeek_generator(first_value, iterator)


if sys.version_info >= (3, 9):
    from argparse import BooleanOptionalAction

else:
    # backport, adapted from argparse sources
    class BooleanOptionalAction (argparse.Action):
        def __init__(self, option_strings, dest, **kwargs):
            
            _option_strings = []
            for option_string in option_strings:
                _option_strings.append(option_string)
                
                if option_string.startswith('--'):
                    option_string = '--no-' + option_string[2:]
                    _option_strings.append(option_string)
            
            super().__init__(option_strings=_option_strings, dest=dest, nargs=0, **kwargs)
        
        def __call__(self, parser, namespace, values, option_string=None):
            if option_string in self.option_strings:
                setattr(namespace, self.dest, not option_string.startswith('--no-'))
        
        def format_usage(self):
            return ' | '.join(self.option_strings)
