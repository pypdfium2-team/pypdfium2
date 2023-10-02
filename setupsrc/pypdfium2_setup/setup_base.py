# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import setuptools
from pathlib import Path
from wheel.bdist_wheel import bdist_wheel

sys.path.insert(0, str(Path(__file__).parents[1]))
# TODO consider dotted access?
from pypdfium2_setup.packaging_base import *


def bdist_factory(pl_name):
    
    class pypdfium_bdist (bdist_wheel):
        
        def finalize_options(self, *args, **kws):
            bdist_wheel.finalize_options(self, *args, **kws)
            # root_is_pure: redundant, covered by BinaryDistribution below - TODO consider removal
            self.root_is_pure = False
        
        def get_tag(self, *args, **kws):
            return "py3", "none", get_wheel_tag(pl_name)
    
    return pypdfium_bdist


# Use a custom distclass declaring we have a binary extension, to prevent modules from being nested in a purelib/ subdirectory in wheels. This also sets `Root-Is-Purelib: false` in the WHEEL file.
class BinaryDistribution (setuptools.Distribution):
    def has_ext_modules(self):
        return True


def get_setup_kws(modnames):
    
    # NOTE Handle python_requires dynamically so we could adjust it depending on which modules are included
    
    if set(modnames) == set(ModulesAll):
        moddirs = {"": "src"}
    else:
        moddirs = {n: f"src/{n}" for n in [ModulesSpec_Dict[n] for n in modnames]}
    
    return dict(
        version = VerNamespace["V_PYPDFIUM2"],
        package_dir = moddirs,
        python_requires = ">= 3.6",
    )


def mkwheel(pl_name, setup_kws):
    
    # NOTE This will not be called for helpers-only installs
    
    emplace_platfiles(pl_name)
    system = plat_to_system(pl_name)
    libname = LibnameForSystem[system]
    
    setuptools.setup(
        package_data = {"pypdfium2_raw": [libname]},
        cmdclass = {"bdist_wheel": bdist_factory(pl_name)},
        distclass = BinaryDistribution,
        **setup_kws,
    )
