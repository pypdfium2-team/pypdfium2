# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import logging
import pypdfium2.raw as pdfium_c
from pypdfium2._lazy import Lazy
from importlib.util import find_spec
from pypdfium2_cli._parsers import (
    add_input,
    get_input,
)

logger = logging.getLogger("pypdfium2_cli")
HAVE_TABULATE = bool(find_spec("tabulate"))

def attach(parser):
    add_input(parser, pages=True)
    # parser.add_argument(
    #     "--class",
    #     nargs = "+",
    #     choices = ("embedded", "non-embedded"),
    #     default = (),
    # )


def _get_fonts_iter(all_fonts):
    for base_name, fontobj in all_fonts.items():
        source = "embedded" if fontobj.is_embedded else "system"
        yield base_name, fontobj.get_family_name(), fontobj.get_weight(), source


def main(args):
    pdf = get_input(args)
    
    # depending on how long the PDF is, this is slow
    # cf. https://issues.chromium.org/issues/460743388#comment5
    # TODO use https://pdfium-review.googlesource.com/c/pdfium/+/138550 once it is available
    logger.debug("Gathering fonts from pages...")
    all_fonts = {}
    for i in args.pages:
        page = pdf[i]
        for textobj in page.get_objects(filter=(pdfium_c.FPDF_PAGEOBJ_TEXT,)):
            fontobj = textobj.get_font()
            all_fonts[fontobj.get_base_name()] = fontobj
    
    headers = ("Base name", "Family name", "Weight", "Source")
    fonts_iter = _get_fonts_iter(all_fonts)
    if HAVE_TABULATE:
        print(Lazy.tabulate(fonts_iter, headers=headers, stralign="left", tablefmt="pretty"))
    else:
        print(headers)
        for entry in fonts_iter:
            print(entry)
