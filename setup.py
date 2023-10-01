#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# NOTE setuptools may, unfortunately, run this code several times (if using PEP 517 style setup).

import os
import sys
import setuptools
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "setupsrc"))
from pypdfium2_setup.emplace import get_pdfium
from pypdfium2_setup.packaging_base import (
    # TODO consider glob import or dotted access?
    purge_pdfium_versions,
    PlatSpec_EnvVar,
    PlatTarget_None,
    ModulesSpec_EnvVar,
    ModulesAll,
    ModuleRaw,
)


def main():
    
    from pypdfium2_setup.setup_base import mkwheel, get_setup_kws
    
    plat_spec = os.environ.get(PlatSpec_EnvVar, "")
    modnames = os.environ.get(ModulesSpec_EnvVar, "")
    if modnames:
        modnames = modnames.split(",")
        assert set(modnames).issubset(ModulesAll)
    else:
        modnames = ModulesAll
    
    setup_kws = get_setup_kws(modnames)
    
    if plat_spec == PlatTarget_None or ModuleRaw not in modnames:
        # NOTE currently this will implicitly include the bindings file if present in the source tree - this should be taken into account if a pure sdist is desired
        # TODO consider if we can make this more explicit, e.g. split in a mode that strictly excludes all platform files, and another that always includes bindings?
        purge_pdfium_versions()
        setuptools.setup(**setup_kws)
    else:
        pl_name = get_pdfium(plat_spec)
        mkwheel(pl_name, setup_kws)


if __name__ == "__main__":
    main()
