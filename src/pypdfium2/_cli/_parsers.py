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
        help = "If given, pass in a callable returning the object, instead of the object directly. This is useful to handle buffer input when multiprocessing is involved."
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
    
    def __init__(self, orig_input, inmode):
        self._orig_input, self._inmode, self._to_close = orig_input, inmode, []
    
    def __call__(self):
        input, inmode = self._orig_input, self._inmode
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
            buffer.close()
        elif inmode is InputMode.BYTES:
            input = input.read_bytes()
        elif inmode is InputMode.BYTEARRAY:
            input = bytearray(input.read_bytes())
        elif inmode is InputMode.MEMVIEW:
            input = memoryview( input.read_bytes() )
        elif inmode is InputMode.MEMVIEW_W:
            input = memoryview(bytearray( input.read_bytes() ))
        elif inmode is InputMode.SHMEM:
            buffer = input.open("rb")
            size = buffer.seek(0, os.SEEK_END)
            buffer.seek(0)
            input = SharedMemory(create=True, size=size)
            self._to_close.append(_destroy_shmem(input))
            buffer.readinto(input.buf)  # memoryview of mmap
            buffer.close()
        else:
            assert False
        return input


class _destroy_shmem:
    # safety check to ensure we don't have a wrong object also implementing unlink (e.g. Path)
    def __init__(self, shmem):
        self._shmem = shmem
        assert isinstance(self._shmem, SharedMemory)
    def __call__(self):
        self._shmem.unlink()


def get_input(args, **kwargs):
    
    args.input_mode = InputMode[args.input_mode.upper()]
    callable = input_maker(
        args.input.expanduser().resolve(),
        inmode = args.input_mode,
    )
    input = callable() if args.input_direct else callable
    pdf = pdfium.PdfDocument(input, password=args.password, autoclose=True, to_close=callable._to_close, **kwargs)
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
