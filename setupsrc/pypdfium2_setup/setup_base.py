# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import setuptools
from pathlib import Path
from wheel.bdist_wheel import bdist_wheel

sys.path.insert(0, str(Path(__file__).parents[1]))
from pypdfium2_setup.packaging_base import (
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
    
    pl_dir = DataTree / pl_name
    if not pl_dir.exists():
        raise RuntimeError(f"Missing platform directory {pl_name} - you might have forgotten to run update_pdfium.py")
    
    ver_file = pl_dir / VerStatusFileName
    if not ver_file.exists():
        raise RuntimeError(f"Missing PDFium version file for {pl_name}")
    
    ver_changes = dict()
    ver_changes["V_LIBPDFIUM"] = ver_file.read_text().strip()
    if pl_name == PlatformNames.sourcebuild:
        ver_changes["V_BUILDNAME"] = "source"
    else:
        ver_changes["V_BUILDNAME"] = "pdfium-binaries"
    set_versions(ver_changes)
    
    clean_artefacts()
    copy_platfiles(pl_name)
    
    setuptools.setup(
        package_data = {"": [libname]},
        cmdclass = {"bdist_wheel": bdist_factory(pl_name)},
        distclass = BinaryDistribution,
        **SetupKws,
    )
