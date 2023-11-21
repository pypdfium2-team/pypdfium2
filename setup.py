# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# NOTE Unfortunately, pip may run setup.py multiple times with different commands (dist_info, bdist_wheel).
# However, guarding code depending on command is tricky. You'd need to be careful not to cause inconsistent data. Also, it's hard to tell which command runs first because other tools (e.g. build) may run just bdist_wheel.

import os
import sys
import getpass
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
            # note that we have to rewrite the version file rather than use a global variable because the cmdclass is invoked only after preparing code
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


def run_setup(modnames, bin_spec, dist_flavor):
    
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
    
    if modnames == [ModuleHelpers] and bin_spec.pl_name != ExtPlats.sdist:
        kwargs["name"] += "_helpers"
        kwargs["description"] += " (helpers module)"
        kwargs["install_requires"] += ["pypdfium2_raw"]
    elif modnames == [ModuleRaw]:
        kwargs["name"] += "_raw"
        kwargs["description"] += " (raw module)"
        kwargs["version"] = str(bin_spec.version)
    
    if ModuleHelpers in modnames:
        # is_editable = None: unknown/fallback in case the cmdclass is not reached
        helpers_info = get_helpers_info()
        helpers_info["dist_flavor"] = dist_flavor
        helpers_info["is_editable"] = None
        write_json(ModuleDir_Helpers/VersionFN, helpers_info)
        kwargs["version"] = merge_tag(helpers_info, mode="py")
        kwargs["cmdclass"]["build_py"] = pypdfium_build_py
        kwargs["package_dir"]["pypdfium2"] = "src/pypdfium2"
        kwargs["package_data"]["pypdfium2"] = [VersionFN]
        kwargs["entry_points"] = dict(console_scripts=["pypdfium2 = pypdfium2.__main__:cli_main"])
    if ModuleRaw in modnames:
        # FIXME not sure if managing creator/location this way is good? the alternative would be to add them directly on the initial write...
        raw_info = read_json(ModuleDir_Raw/VersionFN)
        raw_info["creator"] = bin_spec.creator
        raw_info["location"] = "external" if ExtPlats.system else "bundled"
        write_json(ModuleDir_Raw/VersionFN, raw_info)
        kwargs["package_dir"]["pypdfium2_raw"] = "src/pypdfium2_raw"
    
    if ModuleRaw not in modnames or bin_spec.pl_name == ExtPlats.sdist:
        kwargs["exclude_package_data"] = {"pypdfium2_raw": PLATFILES_GLOB}
        if bin_spec.pl_name == ExtPlats.sdist:
            kwargs["license_files"] += LICENSES_SDIST
    elif bin_spec.pl_name == ExtPlats.system:
        kwargs["package_data"]["pypdfium2_raw"] = [VersionFN, BindingsFN]
    else:
        sys_name = plat_to_system(bin_spec.pl_name)
        libname = LibnameForSystem[sys_name]
        kwargs["package_data"]["pypdfium2_raw"] = [VersionFN, BindingsFN, libname]
        kwargs["cmdclass"]["bdist_wheel"] = bdist_factory(bin_spec.pl_name)
        kwargs["distclass"] = BinaryDistribution
        kwargs["license"] = f"({kwargs['license']}) AND LicenseRef-PdfiumThirdParty"
        kwargs["license_files"] += LICENSES_WHEEL
    
    if "pypdfium2" in kwargs["package_data"]:
        assert_exists(ModuleDir_Helpers, kwargs["package_data"]["pypdfium2"])
    if "pypdfium2_raw" in kwargs["package_data"]:
        assert_exists(ModuleDir_Raw, kwargs["package_data"]["pypdfium2_raw"])
    
    setuptools.setup(**kwargs)


def main():
    
    spec = parse_bin_spec( os.environ.get(PlatSpec_EnvVar, "") )
    modnames = parse_modspec( os.environ.get(ModulesSpec_EnvVar, "") )
    dist_flavor = os.environ.get(FlavorSpec_EnvVar, "")
    if not dist_flavor:
        # Flavor not given - probably an end user, or a third-party distributor. Try to give some identification by encoding host username and platform.
        dist_flavor = f"caller.{getpass.getuser()}.{Host.platform}"
        print(f"Warning: dist flavor not given, setting to {dist_flavor!r}", file=sys.stderr)
    
    # NOTE in principle, it may be possible to achieve the same as `prepared!` by just filling the data/ cache manually, but this is more explicit, formally disabling the generating code paths
    # TODO just handle down spec to the functions?
    if ModuleRaw in modnames and spec.with_prepare and spec.pl_name != ExtPlats.sdist:
        prepare_setup(spec.pl_name, spec.version, spec.use_v8)
    run_setup(modnames, spec, dist_flavor)


if __name__ == "__main__":
    main()
