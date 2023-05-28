# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import setuptools
from pathlib import Path
from wheel.bdist_wheel import bdist_wheel

sys.path.insert(0, str(Path(__file__).parents[1]))
# TODO? consider glob import or dotted access
from pypdfium2_setup.packaging_base import (
    VerNamespace,
    LibnameForSystem,
    plat_to_system,
    get_wheel_tag,
    emplace_platfiles,
)


def bdist_factory(pl_name):
    
    class pypdfium_bdist (bdist_wheel):
        
        def finalize_options(self, *args, **kws):
            bdist_wheel.finalize_options(self, *args, **kws)
            self.root_is_pure = False
        
        def get_tag(self, *args, **kws):
            return "py3", "none", get_wheel_tag(pl_name)
    
    return pypdfium_bdist


class BinaryDistribution (setuptools.Distribution):
    def has_ext_modules(self):
        return True


SetupKws = dict(
    version = VerNamespace["V_PYPDFIUM2"],
)


def mkwheel(pl_name):
    
    emplace_platfiles(pl_name)
    
    system = plat_to_system(pl_name)
    libname = LibnameForSystem[system]
    
    setuptools.setup(
        package_data = {"": [libname]},
        cmdclass = {"bdist_wheel": bdist_factory(pl_name)},
        distclass = BinaryDistribution,
        **SetupKws,
    )
