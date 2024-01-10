# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# NOTE Unfortunately, pip may run setup.py multiple times with different commands (dist_info, bdist_wheel).
# However, guarding code depending on command is tricky. You'd need to be careful not to cause inconsistent data. Also, it's hard to tell which command runs first because other tools (e.g. build) may run just bdist_wheel.

import os
import sys
from pathlib import Path
import setuptools
from wheel.bdist_wheel import bdist_wheel
from setuptools.command.build_py import build_py as build_py_orig

sys.path.insert(0, str(Path(__file__).parent / "setupsrc"))
from pypdfium2_setup.emplace import prepare_setup
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
        
        if hasattr(self, "editable_mode"):
            helpers_info = read_json(ModuleDir_Helpers/VersionFN)
            helpers_info["is_editable"] = bool(self.editable_mode)
            write_json(ModuleDir_Helpers/VersionFN, helpers_info)
        else:
            print("!!! Warning: cmdclass does not provide `editable_mode` attribute. Please file a bug report.")
        
        build_py_orig.run(self, *args, **kwargs)


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

PLATFILES_GLOB = [BindingsFN, VersionFN, *LibnameForSystem.values()]


def assert_exists(dir, data_files):
    missing = [f for f in data_files if not (dir/f).exists()]
    if missing:
        assert False, f"Missing data files: {missing}"


def run_setup(modnames, pl_name, pdfium_ver):
    
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
    
    if modnames == [ModuleHelpers] and pl_name != ExtPlats.sdist:
        # do not do this for sdist (none)
        kwargs["name"] += "_helpers"
        kwargs["description"] += " (helpers module)"
        kwargs["install_requires"] += ["pypdfium2_raw"]
    elif modnames == [ModuleRaw]:
        kwargs["name"] += "_raw"
        kwargs["description"] += " (raw module)"
        kwargs["version"] = str(pdfium_ver)
    
    if ModuleHelpers in modnames:
        # is_editable = None: unknown/fallback in case the cmdclass is not reached
        helpers_info = get_helpers_info()
        if pl_name == ExtPlats.sdist:
            # ignore dirty state due to craft_packages::tmp_ctypesgen_pin()
            helpers_info["dirty"] = False
        kwargs["version"] = merge_tag(helpers_info, mode="py")
        helpers_info["is_editable"] = None
        write_json(ModuleDir_Helpers/VersionFN, helpers_info)
        kwargs["cmdclass"]["build_py"] = pypdfium_build_py
        kwargs["package_dir"]["pypdfium2"] = "src/pypdfium2"
        kwargs["package_data"]["pypdfium2"] = [VersionFN]
        kwargs["entry_points"] = dict(console_scripts=["pypdfium2 = pypdfium2.__main__:cli_main"])
    if ModuleRaw in modnames:
        kwargs["package_dir"]["pypdfium2_raw"] = "src/pypdfium2_raw"
    
    if ModuleRaw not in modnames or pl_name == ExtPlats.sdist:
        kwargs["exclude_package_data"] = {"pypdfium2_raw": PLATFILES_GLOB}
        if pl_name == ExtPlats.sdist:
            kwargs["license_files"] += LICENSES_SDIST
    elif pl_name == ExtPlats.system:
        kwargs["package_data"]["pypdfium2_raw"] = [VersionFN, BindingsFN]
    else:
        sys_name = plat_to_system(pl_name)
        libname = LibnameForSystem[sys_name]
        kwargs["package_data"]["pypdfium2_raw"] = [VersionFN, BindingsFN, libname]
        kwargs["cmdclass"]["bdist_wheel"] = bdist_factory(pl_name)
        kwargs["distclass"] = BinaryDistribution
        kwargs["license"] = f"({kwargs['license']}) AND LicenseRef-PdfiumThirdParty"
        kwargs["license_files"] += LICENSES_WHEEL
    
    if "pypdfium2" in kwargs["package_data"]:
        assert_exists(ModuleDir_Helpers, kwargs["package_data"]["pypdfium2"])
    if "pypdfium2_raw" in kwargs["package_data"]:
        assert_exists(ModuleDir_Raw, kwargs["package_data"]["pypdfium2_raw"])
    
    setuptools.setup(**kwargs)


def main():
    
    pl_spec = os.environ.get(PlatSpec_EnvVar, "")
    modspec = os.environ.get(ModulesSpec_EnvVar, "")
    
    # NOTE in principle, it may be possible to achieve the same as `prepared!` by just filling the data/ cache manually, but this is more explicit, formally disabling the generating code paths
    with_prepare, pl_name, pdfium_ver, use_v8 = parse_pl_spec(pl_spec)
    modnames = parse_modspec(modspec)
    
    if ModuleRaw in modnames and with_prepare and pl_name != ExtPlats.sdist:
        prepare_setup(pl_name, pdfium_ver, use_v8)
    run_setup(modnames, pl_name, pdfium_ver)


if __name__ == "__main__":
    main()
