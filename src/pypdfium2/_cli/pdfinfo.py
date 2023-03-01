# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2.raw as pdfium_c
from pypdfium2._helpers._internal import consts
from pypdfium2._cli._parsers import (
    add_input,
    add_n_digits,
    get_input,
    round_list,
)


def attach(parser):
    add_input(parser)
    add_n_digits(parser)


def main(args):
    
    pdf = get_input(args)
    print(f"Page Count: {len(pdf)}")
    print(f"PDF Version: {pdf.get_version() / 10}")
    
    id_permanent = pdf.get_identifier(pdfium_c.FILEIDTYPE_PERMANENT)
    id_changing  = pdf.get_identifier(pdfium_c.FILEIDTYPE_CHANGING)
    print(f"ID (permanent): {id_permanent}")
    print(f"ID (changing):  {id_changing}")
    print(f"ID match? - {id_permanent == id_changing}")
    print(f"Tagged? - {pdf.is_tagged()}")
    
    pagemode = pdf.get_pagemode()
    if pagemode != pdfium_c.PAGEMODE_USENONE:
        print(f"Page Mode: {consts.PageModeToStr.get(pagemode)}")
    
    # FIXME use support model once implemented properly
    formtype = pdfium_c.FPDF_GetFormType(pdf)
    if formtype != pdfium_c.FORMTYPE_NONE:
        print(f"Forms: {consts.FormTypeToStr.get(formtype)}")
    
    metadata = pdf.get_metadata_dict(skip_empty=True)
    if len(metadata) > 0:
        print("Metadata:")
        for key, value in metadata.items():
            print(f"    {key}: {value}")
    
    for i in args.pages:
        
        print(f"\n# Page {i+1}")
        page = pdf[i]
        
        size = round_list(page.get_size(), args.n_digits)
        print(f"Size: {size}")
        print(f"Rotation: {page.get_rotation()}")
        
        bbox = round_list(page.get_bbox(), args.n_digits)
        print(f"Bounding Box: {bbox}")
        
        mediabox = round_list(page.get_mediabox(), args.n_digits)
        print(f"MediaBox: {mediabox}")
        
        cropbox = round_list(page.get_cropbox(), args.n_digits)
        if cropbox != mediabox:
            print(f"CropBox: {cropbox}")
        
        bleedbox = round_list(page.get_bleedbox(), args.n_digits)
        if bleedbox != cropbox:
            print(f"BleedBox: {bleedbox}")
        
        trimbox = round_list(page.get_trimbox(), args.n_digits)
        if trimbox != cropbox:
            print(f"TrimBox: {trimbox}")
        
        artbox = round_list(page.get_artbox(), args.n_digits)
        if artbox != cropbox:
            print(f"ArtBox: {artbox}")
