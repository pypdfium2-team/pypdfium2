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
    print("Page Count: %s" % len(pdf))
    print("PDF Version: %s" % str(pdf.get_version() / 10))
    
    id_permanent = pdf.get_identifier(pdfium_c.FILEIDTYPE_PERMANENT)
    id_changing  = pdf.get_identifier(pdfium_c.FILEIDTYPE_CHANGING)
    print("ID (permanent): %s" % id_permanent)
    print("ID (changing):  %s" % id_changing)
    print("ID match? - %s" % (id_permanent == id_changing))
    print("Tagged? - %s" % pdf.is_tagged())
    
    pagemode = pdf.get_pagemode()
    if pagemode != pdfium_c.PAGEMODE_USENONE:
        print("Page Mode: %s" % consts.PageModeToStr.get(pagemode))
    
    if pdf._has_forms:
        print("Forms: %s" % consts.FormTypeToStr.get(pdf.formtype))
    
    metadata = pdf.get_metadata_dict(skip_empty=True)
    pad = " " * 4
    if len(metadata) > 0:
        print("Metadata:")
        for key, value in metadata.items():
            print(pad + "%s: %s" % (key, value))
    
    for i in args.pages:
        
        print()
        page = pdf[i]
        size = round_list(page.get_size(), args.n_digits)
        
        print("# Page %s" % (i+1, ))
        print("Size: %s" % (size, ))
        print("Rotation: %s" % (page.get_rotation(), ))
        
        bbox = round_list(page.get_bbox(), args.n_digits)
        print("Bounding Box: %s" % (bbox, ))
        
        mediabox = round_list(page.get_mediabox(), args.n_digits)
        cropbox  = round_list(page.get_cropbox(),  args.n_digits)
        bleedbox = round_list(page.get_bleedbox(), args.n_digits)
        trimbox  = round_list(page.get_trimbox(),  args.n_digits)
        artbox   = round_list(page.get_artbox(),   args.n_digits)
        
        print("MediaBox: %s" % (mediabox, ))
        if cropbox != mediabox:
            print("CropBox: %s" % (cropbox, ))
        if bleedbox != cropbox:
            print("BleedBox: %s" % (bleedbox, ))
        if trimbox != cropbox:
            print("TrimBox: %s" % (trimbox, ))
        if artbox != cropbox:
            print("ArtBox: %s" % (artbox, ))
