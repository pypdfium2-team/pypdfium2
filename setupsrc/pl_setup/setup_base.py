# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import setuptools
from os.path import abspath, dirname
from wheel.bdist_wheel import bdist_wheel

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from pl_setup.packaging_base import (
    VerNamespace,
    LibnameForSystem,
    plat_to_system,
    get_wheel_tag,
    clean_artefacts,
    copy_platfiles,
)


def bdist_factory(pl_name):
    
    class pypdfium_bdist (bdist_wheel):
        
        def finalize_options(self, *args, **kws):
            bdist_wheel.finalize_options(self, *args, **kws)
            self.plat_name_supplied = True
            self.root_is_pure = False
        
        def get_tag(self, *args, **kws):
            return "py3", "none", get_wheel_tag(pl_name)
    
    return pypdfium_bdist


SetupKws = dict(
    version = VerNamespace["V_PYPDFIUM2"],
)


class BinaryDistribution (setuptools.Distribution):
    def has_ext_modules(self):
        return True


def mkwheel(pl_name):
    
    # NOTE this will fail in case of sourcebuild with unknown host system
    system = plat_to_system(pl_name)
    libname = LibnameForSystem[system]
    
    clean_artefacts()
    copy_platfiles(pl_name)
    
    setuptools.setup(
        package_data = {"": [libname]},
        cmdclass = {"bdist_wheel": bdist_factory(pl_name)},
        distclass = BinaryDistribution,
        **SetupKws,
    )
