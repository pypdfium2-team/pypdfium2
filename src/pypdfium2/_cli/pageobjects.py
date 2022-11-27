# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

from enum import Enum
import pypdfium2._helpers as pdfium
from pypdfium2._helpers._internal import utils, consts
from pypdfium2._cli._parsers import add_input, get_input


class InfoParams (Enum):
    pos = 0
    imageinfo = 1


def attach(parser):
    
    obj_types = list( consts.ObjectTypeToConst.keys() )
    
    add_input(parser, pages=True)
    parser.add_argument(
        "--filter",
        nargs = "+",
        metavar = "T",
        choices = obj_types,
        default = obj_types,
        help = "Object types to include. Choices: %s" % (obj_types, ),
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


def main(args):
    
    pdf = get_input(args)
    args.filter = [consts.ObjectTypeToConst[t] for t in args.filter]
    
    show_pos = (InfoParams.pos in args.info)
    show_imageinfo = (InfoParams.imageinfo in args.info)
    total_count = 0
    
    for i in args.pages:
        
        page = pdf.get_page(i)
        obj_searcher = page.get_objects(
            filter = args.filter,
            max_depth = args.max_depth,
        )
        preamble = "# Page %s\n" % (i+1)
        count = 0
        
        for obj in obj_searcher:
            
            pad_0 = "    " * obj.level
            pad_1 = pad_0 + "    "
            print(preamble + pad_0 + consts.ObjectTypeToStr[obj.type])
            
            if show_pos:
                print("%sPosition: %s" % (pad_1, obj.get_pos()))
            
            if show_imageinfo and isinstance(obj, pdfium.PdfImage):
                print("%sFilters: %s" % (pad_1, obj.get_filters()))
                metadata = obj.get_metadata()
                print(utils.image_metadata_to_str(metadata, pad=pad_1))
            
            count += 1
            preamble = ""
        
        if count > 0:
            print("-> Count: %s\n" % count)
            total_count += count
    
    print("-> Total count: %s" % total_count)
