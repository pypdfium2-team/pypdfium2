# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pypdfium2.raw as pdfium_c
from pypdfium2._helpers._internal import consts
from pypdfium2._cli._parsers import add_input, get_input


def attach(parser):
    add_input(parser)


def main(args):
    
    pdf = get_input(args)
    print("Page Count: %s" % len(pdf))
    print("Page Mode: %s" % consts.PageModeToStr[pdf.get_pagemode()])
    
    formtype = pdf.get_formtype()
    if formtype != pdfium_c.FORMTYPE_NONE:
        print("Forms: %s" % consts.FormTypeToStr[formtype])
    
    metadata = pdf.get_metadata_dict(skip_empty=True)
    pad = " " * 4
    if len(metadata) > 0:
        print("Metadata:")
        for key, value in metadata.items():
            print(pad + "%s: %s" % (key, value))
    
    for i in args.pages:
        
        print()
        page = pdf[i]
        
        print("# Page %s" % (i+1, ))
        print("Size: %s" % (page.get_size(), ))
        print("Rotation: %s" % (page.get_rotation(), ))
        print("Bounding Box: %s" % (page.get_bbox(), ))
        
        mediabox = page.get_mediabox()
        cropbox = page.get_cropbox()
        bleedbox = page.get_bleedbox()
        trimbox = page.get_trimbox()
        artbox = page.get_artbox()
        
        print("MediaBox: %s" % (mediabox, ))
        if cropbox != mediabox:
            print("CropBox: %s" % (cropbox, ))
        if bleedbox != cropbox:
            print("BleedBox: %s" % (bleedbox, ))
        if trimbox != cropbox:
            print("TrimBox: %s" % (trimbox, ))
        if artbox != cropbox:
            print("ArtBox: %s" % (artbox, ))
