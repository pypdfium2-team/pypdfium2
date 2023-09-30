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
    BinarySpec_EnvVar,
    PlatformTarget_None,
    ModulesSpec_EnvVar,
)


def main():
    
    from pypdfium2_setup.setup_base import mkwheel, get_setup_kws
    
    binary_spec = os.environ.get(BinarySpec_EnvVar, "")
    modules_spec = os.environ.get(ModulesSpec_EnvVar, "")
    if modules_spec:
       modules_spec = modules_spec.split(",")
    
    if binary_spec == PlatformTarget_None:
        purge_pdfium_versions()
        setuptools.setup(**get_setup_kws(modules_spec))
        return
    
    pl_name = get_pdfium(binary_spec)
    mkwheel(pl_name, modules_spec)


if __name__ == "__main__":
    main()
