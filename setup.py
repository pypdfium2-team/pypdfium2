# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# NOTE Unfortunately, pip may run setup.py multiple times with different commands (dist_info, bdist_wheel).
# However, guarding code depending on command is tricky. You'd need to be careful not to cause inconsistent data. Also, it's hard to tell which command runs first because other tools (e.g. build) may run just bdist_wheel.

import os
import sys
import traceback
import subprocess
from pathlib import Path
import setuptools
from wheel.bdist_wheel import bdist_wheel
from setuptools.command.build_py import build_py as build_py_orig

sys.path.insert(0, str(Path(__file__).parent / "setupsrc"))
from pypdfium2_setup.emplace import get_pdfium
from pypdfium2_setup.packaging_base import *


# Use a custom distclass declaring we have a binary extension, to prevent modules from being nested in a purelib/ subdirectory in wheels. This also sets `Root-Is-Purelib: false` in the WHEEL file.

class BinaryDistribution (setuptools.Distribution):
    
    def has_ext_modules(self):
        return True


def bdist_factory(pl_name):
    
    class pypdfium_bdist (bdist_wheel):
        
        def finalize_options(self, *args, **kws):
            bdist_wheel.finalize_options(self, *args, **kws)
        
        def get_tag(self, *args, **kws):
            return "py3", "none", get_wheel_tag(pl_name)
    
    return pypdfium_bdist


class pypdfium_build_py (build_py_orig):
        
    def run(self, *args, **kwargs):
        
        if self.editable_mode:
            # TODO consider merging with data_source?
            # TODO consider setting n_commits/hash to inf/editable due to high uncertainty? either here or in the receiver
            helpers_info = read_json(ModuleDir_Helpers/VersionFN)
            helpers_info["is_editable"] = True
            write_json(ModuleDir_Helpers/VersionFN, helpers_info)
        
        build_py_orig.run(self, *args, **kwargs)


def get_helpers_info():
    
    # TODO consider adding some checks against record
    
    have_git_describe = False
    if HAVE_GIT_REPO:
        try:
            helpers_info = parse_git_tag()
        except subprocess.CalledProcessError:
            print("Version uncertain: git describe failure - possibly a shallow checkout", file=sys.stderr)
            traceback.print_exc()
        else:
            have_git_describe = True
            helpers_info["data_source"] = "git"
    else:
        print("Version uncertain: git repo not available.")
    
    if not have_git_describe:
        ver_file = ModuleDir_Helpers / VersionFN
        if ver_file.exists():
            print("Falling back to given version info (e.g. sdist).", file=sys.stderr)
            helpers_info = read_json(ver_file)
            helpers_info["data_source"] = "given"
        else:
            print("Falling back to autorelease record.", file=sys.stderr)
            record = read_json(AR_RecordFile)
            helpers_info = parse_given_tag(record["tag"])
            helpers_info["data_source"] = "record"
    
    return helpers_info


# semi-static metadata
PROJECT_DESC = "Python bindings to PDFium"
LICENSES_SHARED = (
    "LICENSES/Apache-2.0.txt",
    "LICENSES/BSD-3-Clause.txt",
    "LICENSES/CC-BY-4.0.txt",
)
LICENSES_WHEEL = (
    "LICENSES/LicenseRef-PdfiumThirdParty.txt",
    ".reuse/dep5-wheel",
)
LICENSES_SDIST = (
    "LICENSES/LicenseRef-FairUse.txt",
    ".reuse/dep5",
)


def main():
    
    pl_name = os.environ.get(PlatSpec_EnvVar, "")
    modnames = os.environ.get(ModulesSpec_EnvVar, "")
    if modnames:
        modnames = modnames.split(",")
        assert set(modnames).issubset(ModulesAll)
    else:
        modnames = ModulesAll
    assert len(modnames) in (1, 2)
    
    kwargs = dict(
        name = "pypdfium2",
        description = "Python bindings to PDFium",
        license = "Apache-2.0 OR BSD-3-Clause",
        license_files = LICENSES_SHARED,
        python_requires = ">= 3.6",
        cmdclass = {},
        package_dir = {},
        package_data = {},
        install_requires = [],
    )
    
    # TODO consider using pdfium version for raw-only?
    helpers_info = get_helpers_info()
    kwargs["version"] = merge_tag(helpers_info, mode="py")
    
    if modnames == [ModuleHelpers]:
        kwargs["description"] += " (helpers module)"
        kwargs["install_requires"] += ["pypdfium2_raw"]
    elif modnames == [ModuleRaw]:
        kwargs["name"] += "_raw"
        kwargs["description"] += " (raw module)"
    
    with_helpers = ModuleHelpers in modnames
    with_raw = ModuleRaw in modnames and pl_name != PlatTarget_None
    if with_helpers:
        helpers_info["is_editable"] = False  # default
        write_json(ModuleDir_Helpers/VersionFN, helpers_info)
        kwargs["cmdclass"]["build_py"] = pypdfium_build_py
        kwargs["package_dir"]["pypdfium2"] = "src/pypdfium2"
        kwargs["package_data"]["pypdfium2"] = [VersionFN]
    if with_raw:
        kwargs["package_dir"]["pypdfium2_raw"] = "src/pypdfium2_raw"
    
    if "pypdfium2_raw" not in kwargs["package_dir"]:
        kwargs["exclude_package_data"] = {"pypdfium2_raw": [VersionFN, BindingsFN, *LibnameForSystem.values()]}
        if pl_name == PlatTarget_None:
            kwargs["license_files"] += LICENSES_SDIST
    elif pl_name == PlatTarget_System:
        # TODO generate bindings/version here according to some caller input?
        assert (ModuleDir_Raw/BindingsFN).exists() and (ModuleDir_Raw/VersionFN).exists(), "Bindings and version currently must be prepared by caller for sys target."
        kwargs["package_data"]["pypdfium2_raw"] = [BindingsFN, VersionFN]
    else:
        pl_name = get_pdfium(pl_name)
        emplace_platfiles(pl_name)
        sys_name = plat_to_system(pl_name)
        libname = LibnameForSystem[sys_name]
        kwargs["package_data"]["pypdfium2_raw"] = [VersionFN, BindingsFN, libname]
        kwargs["cmdclass"]["bdist_wheel"] = bdist_factory(pl_name)
        kwargs["distclass"] = BinaryDistribution
        kwargs["license"] = f"({kwargs['license']}) AND LicenseRef-PdfiumThirdParty"
        kwargs["license_files"] += LICENSES_WHEEL
    
    setuptools.setup(**kwargs)


if __name__ == "__main__":
    main()
