# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import ast
from pypdfium2 import _namespace as pdfium
from os.path import (
    join,
    abspath,
    basename,
    splitext,
)


def rotation_type(string):
    rotation = int(string)
    if rotation not in (0, 90, 180, 270):
        raise ValueError("Invalid rotation value %s" % rotation)
    return rotation


def colour_type(string):
    
    if string.lower() == 'none':
        return
    
    else:
        
        colour = ast.literal_eval(string)
        
        if not isinstance(colour, (tuple, list)):
            raise ValueError("Invalid colour type %s. Must be list or tuple." % type(colour))
        if not len(colour) in (3, 4):
            raise ValueError("Invalid number of colour values. Must be 3 or 4.")
        if not all(isinstance(val, int) and 0 <= val <= 255 for val in colour):
            raise ValueError("Colour values must be integers ranging from 0 to 255.")
        
        return colour


def pagetext_type(value):
    
    if not value:
        return
    
    page_indices = []
    splitted = value.split(',')
    
    for page_or_range in splitted:
        
        if '-' in page_or_range:
            
            start, end = page_or_range.split('-')
            start = int(start) - 1
            end = int(end) - 1
            
            if start < end:
                pages = [i for i in range(start, end+1)]
            else:
                pages = [i for i in range(start, end-1, -1)]
            
            page_indices.extend(pages)
        
        else:
            
            page_indices.append(int(page_or_range) - 1)
    
    return page_indices


def attach_parser(subparsers):
    parser = subparsers.add_parser(
        "render",
        help = "Rasterise pages of a PDF file",
    )
    parser.add_argument(
        'inputs',
        nargs = '+',
        help = "PDF documents to render",
    )
    parser.add_argument(
        '--output', '-o',
        type = abspath,
        required = True,
        help = "Output directory where to place the serially numbered images",
    )
    parser.add_argument(
        '--format', '-f',
        default = 'png',
        help = "File extension of the image format to use",
    )
    parser.add_argument(
        '--pages',
        default = None,
        type = pagetext_type,
        help = "Numbers of the pages to render (defaults to all)",
    )
    parser.add_argument(
        '--scale',
        default = 1,
        type = float,
        help = "Define the resolution of the output images. By default, one PDF point (1/72in) is rendered to 1x1 pixel. This factor scales the number of pixels that represent one point.",
    )
    parser.add_argument(
        '--rotation',
        default = 0,
        type = rotation_type,
        help = "Rotate pages by 90, 180 or 270 degrees",
    )
    parser.add_argument(
        '--colour',
        default = (255, 255, 255, 255),
        type = colour_type,
        help = "Page background colour. Defaults to white. It can be given in RGBA format as a sequence of integers ranging from 0 to 255, or it may be 'none' for transparent background."
    )
    parser.add_argument(
        '--no-annotations',
        action = 'store_true',
        help = "Option to prevent rendering of PDF annotations",
    )
    parser.add_argument(
        '--optimise-mode',
        default = pdfium.OptimiseMode.none,
        type = lambda string: pdfium.OptimiseMode[string.lower()],
        help = "Select a rendering optimisation mode (none, lcd_display, printing)",
    )
    parser.add_argument(
        '--greyscale',
        action = 'store_true',
        help = "Whether to render in greyscale mode (no colours)",
    )
    parser.add_argument(
        '--processes',
        default = os.cpu_count(),
        type = int,
        help = "The number of processes to use for rendering (defaults to the number of CPU cores)"
    )


def main(args):
        
    for input_path in args.inputs:
        
        prefix = splitext(basename(input_path))[0] + '_'
        
        renderer = pdfium.render_pdf_topil(
            input_path,
            page_indices = args.pages,
            scale = args.scale,
            rotation = args.rotation,
            colour = args.colour,
            annotations = not args.no_annotations,
            greyscale = args.greyscale,
            optimise_mode = args.optimise_mode,
            n_processes = args.processes,
        )
        
        for image, suffix in renderer:
            output_path = "%s.%s" % (join(args.output, prefix+suffix), args.format)
            image.save(output_path)
            image.close()
