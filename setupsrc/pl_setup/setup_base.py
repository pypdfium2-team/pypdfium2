# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import setuptools
from os.path import (
    join,
    exists,
    abspath,
    dirname,
)
from wheel.bdist_wheel import bdist_wheel

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from pl_setup.packaging_base import (
    DataTree,
    VerNamespace,
    LibnameForSystem,
    VerStatusFileName,
    PlatformNames,
    plat_to_system,
    get_wheel_tag,
    clean_artefacts,
    copy_platfiles,
    set_versions,
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
    
    system = plat_to_system(pl_name)
    libname = LibnameForSystem[system]
    
    pl_dir = join(DataTree, pl_name)
    if not exists(pl_dir):
        raise RuntimeError("Missing platform directory %s - you might have forgotten to run update_pdfium.py" % pl_name)
    
    ver_file = join(pl_dir, VerStatusFileName)
    if not exists(ver_file):
        raise RuntimeError("Missing PDFium version file for %s" % pl_name)
    
    with open(ver_file, "r") as fh:
        v_libpdfium = fh.read().strip()
    
    ver_changes = dict()
    ver_changes["V_LIBPDFIUM"] = str(v_libpdfium)
    ver_changes["IS_SOURCEBUILD"] = (pl_name == PlatformNames.sourcebuild)
    set_versions(ver_changes)
    
    clean_artefacts()
    copy_platfiles(pl_name)
    
    setuptools.setup(
        package_data = {"": [libname]},
        cmdclass = {"bdist_wheel": bdist_factory(pl_name)},
        distclass = BinaryDistribution,
        **SetupKws,
    )
