# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import mmap
import ctypes
import logging
from enum import Enum
from pathlib import Path
from multiprocessing.shared_memory import SharedMemory
import pypdfium2._helpers as pdfium

logger = logging.getLogger(__name__)


class InputMode (Enum):
    STRPATH   = "strpath"
    PATH      = "path"
    BUFFER    = "buffer"
    MMAP      = "mmap"
    CTYPES    = "ctypes"
    BYTES     = "bytes"
    BYTEARRAY = "bytearray"
    MEMVIEW   = "memview"
    MEMVIEW_W = "memview_w"
    SHMEM     = "shmem"


def add_input(parser, pages=True):
    parser.add_argument(
        "input",
        type = Path,
        help = "Input PDF document",
    )
    parser.add_argument(
        "--input-mode",
        default = InputMode.PATH.value,
        choices = [m.lower() for m in InputMode.__members__],
        help = "The file access strategy to use."
    )
    parser.add_argument(
        "--input-callable",
        dest = "input_direct",
        action = "store_false",
        # TODO help
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


class input_maker:
    
    # to batch test all input types:
    # inmodes='strpath path buffer mmap ctypes bytes bytearray memview memview_w shmem'
    # for INMODE in $inmodes; do echo "$INMODE"; pypdfium2 toc --input-mode $INMODE "tests/resources/toc.pdf"; printf "\n"; done
    
    def __init__(self, input, inmode):
        self.input, self.inmode = input, inmode
    
    def __call__(self):
        input, inmode = self.input, self.inmode
        if inmode is InputMode.STRPATH:
            input = str(input)
        elif inmode is InputMode.PATH:
            assert isinstance(input, Path)
        elif inmode is InputMode.BUFFER:
            input = input.open("rb")
        elif inmode is InputMode.MMAP:
            fh = input.open("r+b")
            input = mmap.mmap(fh.fileno(), 0)
        elif inmode is InputMode.CTYPES:
            buffer = input.open("rb")
            size = buffer.seek(0, os.SEEK_END)
            buffer.seek(0)
            input = (ctypes.c_ubyte * size)()
            buffer.readinto(input)
        elif inmode is InputMode.BYTES:
            input = input.read_bytes()
        elif inmode is InputMode.BYTEARRAY:
            input = bytearray(input.read_bytes())
        elif inmode is InputMode.MEMVIEW:
            input = memoryview( input.read_bytes() )
        elif inmode is InputMode.MEMVIEW_W:
            input = memoryview(bytearray( input.read_bytes() ))
        elif inmode is InputMode.SHMEM:
            # FIXME shm object never destoryed before shutdown
            # the problem is, we want to destory it when closing the root document, but not when closing a spawned sub-document
            buffer = input.open("rb")
            size = buffer.seek(0, os.SEEK_END)
            buffer.seek(0)
            input = SharedMemory(create=True, size=size)
            buffer.readinto(input.buf.obj)  # mmap
        else:
            assert False
        return input


def get_input(args, **kwargs):
    
    callable = input_maker(
        input = args.input.expanduser().resolve(),
        inmode = InputMode[args.input_mode.upper()],
    )
    input = callable() if args.input_direct else callable
    pdf = pdfium.PdfDocument(input, password=args.password, autoclose=True, **kwargs)
    logger.debug(f"CLI: created pdf {pdf!r}")

    if "pages" in args and not args.pages:
        args.pages = [i for i in range(len(pdf))]
    
    return pdf


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


def add_n_digits(parser):
    parser.add_argument(
        "--n-digits",
        type = int,
        default = 4,
        help = "Number of digits to which coordinates/sizes shall be rounded",
    )
