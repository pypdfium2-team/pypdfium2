# SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# TODO test-confirm filter and info params

from enum import Enum
import pypdfium2._helpers as pdfium
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i
# TODO? consider dotted access
from pypdfium2._cli._parsers import (
    add_input,
    add_n_digits,
    get_input,
    round_list,
)


class InfoParams (Enum):
    pos = 0
    imageinfo = 1


def attach(parser):
    
    add_input(parser, pages=True)
    add_n_digits(parser)
    
    # TODO think out strategy for choices (see https://github.com/python/cpython/issues/69247)
    obj_types = list( pdfium_i.ObjectTypeToConst.keys() )
    parser.add_argument(
        "--filter",
        nargs = "+",
        metavar = "T",
        choices = obj_types,
        help = f"Object types to include. Choices: {obj_types}",
    )
    parser.add_argument(
        "--max-depth",
        type = int,
        default = 2,
        help = "Maximum recursion depth to consider when descending into Form XObjects.",
    )
    parser.add_argument(
        "--info",
        nargs = "*",
        type = lambda s: InfoParams[s.lower()],
        default = (InfoParams.pos, InfoParams.imageinfo),
        help = "Object details to show (pos, imageinfo).",
    )


def print_img_metadata(metadata, pad=""):
    for attr in pdfium_c.FPDF_IMAGEOBJ_METADATA.__slots__:
        value = getattr(metadata, attr)
        if attr == "colorspace":
            value = pdfium_i.ColorspaceToStr.get(value)
        elif attr == "marked_content_id" and value == -1:
            continue
        print(pad + f"{attr}: {value}\n", end="")


def main(args):
    
    pdf = get_input(args)
    
    # if no filter is given, leave it at None (make a difference in case of unhandled object types)
    if args.filter:
        args.filter = [pdfium_i.ObjectTypeToConst[t] for t in args.filter]
    
    show_pos = (InfoParams.pos in args.info)
    show_imageinfo = (InfoParams.imageinfo in args.info)
    total_count = 0
    
    for i in args.pages:
        
        page = pdf[i]
        obj_searcher = page.get_objects(
            filter = args.filter,
            max_depth = args.max_depth,
        )
        preamble = f"# Page {i+1}\n"
        count = 0
        
        for obj in obj_searcher:
            
            pad_0 = "    " * obj.level
            pad_1 = pad_0 + "    "
            print(preamble + pad_0 + pdfium_i.ObjectTypeToStr.get(obj.type))
            
            if show_pos:
                pos = round_list(obj.get_pos(), args.n_digits)
                print(pad_1 + f"Position: {pos}")
            
            # TODO? also call get_size() for coverage
            if show_imageinfo and isinstance(obj, pdfium.PdfImage):
                print(pad_1 + f"Filters: {obj.get_filters()}")
                metadata = obj.get_metadata()
                print_img_metadata(metadata, pad=pad_1)
            
            count += 1
            preamble = ""
        
        if count > 0:
            print(f"-> Count: {count}\n")
            total_count += count
    
    if total_count > 0:
        print(f"-> Total count: {total_count}")
