# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import logging
from collections import namedtuple
from importlib.util import find_spec
import pypdfium2.raw as pdfium_c
from pypdfium2._lazy import Lazy
from pypdfium2_cli._parsers import (
    add_input,
    get_input,
    pagenums_ranger,
)

logger = logging.getLogger("pypdfium2_cli")
HAVE_TABULATE = bool(find_spec("tabulate"))

FontHolder = namedtuple("FontHolder", ("obj", "pages"))


def attach(parser):
    add_input(parser, pages=True)

def _get_fonts_iter(all_fonts):
    for base_name, fontholder in all_fonts.items():
        fontobj = fontholder.obj
        source = "embedded" if fontobj.is_embedded else "system"
        pages_str = ", ".join(str(p) for p in pagenums_ranger(sorted(fontholder.pages)))
        yield base_name, fontobj.get_family_name(), fontobj.get_weight(), source, pages_str


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
            base_name = fontobj.get_base_name()
            if base_name in all_fonts:
                fontholder = all_fonts[base_name]
            else:
                fontholder = FontHolder(fontobj, set())
                all_fonts[base_name] = fontholder
            fontholder.pages.add(i+1)
    
    headers = ("Base name", "Family name", "Weight", "Source", "Pages")
    fonts_iter = _get_fonts_iter(all_fonts)
    if HAVE_TABULATE:
        print(Lazy.tabulate(fonts_iter, headers=headers, stralign="left", tablefmt="pretty", maxcolwidths=[30, 30, None, None, 80]))
    else:
        logger.info("You may want to install `tabulate` for prettier output.")
        print(headers)
        for entry in fonts_iter:
            print(entry)
