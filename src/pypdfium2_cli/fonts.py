# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import logging
from ctypes import addressof
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
    for fontholder in all_fonts.values():
        fontobj = fontholder.obj
        source = "embedded" if fontobj.is_embedded else "system"
        pages_str = ", ".join(str(p) for p in pagenums_ranger(sorted(fontholder.pages)))
        yield fontobj.get_base_name(), fontobj.get_family_name(), fontobj.get_weight(), source, pages_str


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
            addr = addressof(fontobj.raw.contents)
            if addr in all_fonts:
                fontholder = all_fonts[addr]
            else:
                fontholder = FontHolder(fontobj, set())
                all_fonts[addr] = fontholder
            fontholder.pages.add(i+1)
    
    headers = ("Base name", "Family name", "Weight", "Source", "Pages")
    fonts_iter = _get_fonts_iter(all_fonts)
    if HAVE_TABULATE:
        fonts_list = list(fonts_iter)
        if not fonts_list:
            return
        print(Lazy.tabulate(fonts_list, headers=headers, stralign="left", tablefmt="pretty", maxcolwidths=[30, 30, None, None, 80]))
    else:
        logger.info("You may want to install `tabulate` for prettier output.")
        print(headers)
        for entry in fonts_iter:
            print(entry)
