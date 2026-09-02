# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Reading material:
# https://stackoverflow.com/questions/45150304/how-to-force-a-python-wheel-to-be-platform-specific-when-building-it
# https://stackoverflow.com/questions/69647983/how-to-add-platform-specific-package-data-in-setup-py
# https://github.com/tim-mitchell/prebuilt_binaries
# https://stackoverflow.com/a/48015772/15547292
# https://cibuildwheel.pypa.io/en/stable/faq/#actions-you-need-to-perform-before-building
# https://build.pypa.io/en/latest/how-to/config-settings.html#id1

import os
import sys
from pathlib import Path
from functools import partial
import setuptools
from setuptools.command.build_py import build_py as buildpy_orig
try:
    from setuptools.command.bdist_wheel import bdist_wheel
except ImportError:
    from wheel.bdist_wheel import bdist_wheel

sys.path.insert(0, str(Path(__file__).parent/"setupsrc"))
from base import *
import system_pdfium
from emplace import prepare_setup
from tagging import get_wheel_tag


# Use a custom distclass declaring we have a binary extension, to prevent modules from being nested in a purelib/ subdirectory in wheels.
# This will also set `Root-Is-Purelib: false` in the WHEEL file, and make the wheel tag platform specific by default.
# FIXME For some reason, this does not work properly with Python 3.6 / older setuptools - we still get a purelib folder, even though Root-Is-Purelib is false. :(

class BinaryDistribution (setuptools.Distribution):
    
    def has_ext_modules(self):
        return True


def buildpy_factory(pl_name, datagen, helpers_info, package_data):
    
    class pypdfium_buildpy (buildpy_orig):
        
        def run(self, *args, **kwargs):
            if pl_name != ExtPlats.sdist:
                datagen()
                assert_exists(ModuleDir_Raw, package_data["pypdfium2_raw"])
            helpers_info["is_editable"] = getattr(self, "editable_mode", None)
            write_json(ModuleDir_Helpers/VersionFN, helpers_info)
            assert_exists(ModuleDir_Helpers, package_data["pypdfium2"])
            buildpy_orig.run(self, *args, **kwargs)
    
    return pypdfium_buildpy


def bdist_factory(pl_name, dll_path):
    
    class pypdfium_bdist (bdist_wheel):
        
        def finalize_options(self, *args, **kws):
            bdist_wheel.finalize_options(self, *args, **kws)
            # should be handled by the distclass already, but set it again to be on the safe side
            self.root_is_pure = False
        
        def get_tag(self, *args, **kws):
            if pl_name == ExtPlats.sourcebuild:
                # In case of cross-compilation (or even just proper packaging), the caller needs to set the tag.
                plat_tag = os.environ.get("CROSS_TAG")
                # Otherwise, forward the host's tag as provided by bdist_wheel (wraps sysconfig.get_platform())
                if not plat_tag:
                    _py, _abi, plat_tag = bdist_wheel.get_tag(self, *args, **kws)
            else:
                plat_tag = get_wheel_tag(pl_name, dll_path)
            return "py3", "none", plat_tag
    
    return pypdfium_bdist


def assert_exists(dir, data_files):
    missing = tuple(f for f in data_files if not (dir/f).exists())
    if missing:
        assert False, f"Missing data files: {missing}"


LICENSES_SHARED = (
    "LICENSES/Apache-2.0.txt",
    "LICENSES/BSD-3-Clause.txt",
    "LICENSES/CC-BY-4.0.txt",
)
LICENSES_SDIST = (
    # our sdists don't currently include tests, so we don't need to list the other licenses here
    "REUSE.toml",
)


def run_setup(pl_name, datagen):
    
    kwargs = dict(
        name = "pypdfium2",
        description = "Python bindings to PDFium",
        license = "BSD-3-Clause, Apache-2.0, dependency licenses",
        python_requires = ">= 3.6",
        cmdclass = {},
        package_dir = {},
        package_data = {},
    )
    
    license_files = list(LICENSES_SHARED)
    if pl_name == ExtPlats.sdist:
        license_files.extend(LICENSES_SDIST)
    
    helpers_info = get_helpers_info()
    kwargs["version"] = merge_tag(helpers_info, mode="py")
    kwargs["package_dir"]["pypdfium2"] = "src/pypdfium2"
    kwargs["package_dir"]["pypdfium2_cfg"] = "src/pypdfium2_cfg"
    kwargs["package_dir"]["pypdfium2_cli"] = "src/pypdfium2_cli"
    kwargs["package_data"]["pypdfium2"] = (VersionFN, )
    kwargs["entry_points"] = dict(console_scripts=["pypdfium2 = pypdfium2_cli.__main__:cli_main"])
    
    kwargs["package_dir"]["pypdfium2_raw"] = "src/pypdfium2_raw"
    if pl_name == ExtPlats.sdist:
        kwargs["exclude_package_data"] = {"pypdfium2_raw": (VersionFN, *LIBNAME_GLOBS)}
    elif pl_name == ExtPlats.system:
        kwargs["package_data"]["pypdfium2_raw"] = (BindingsFN, VersionFN)
        kwargs["exclude_package_data"] = {"pypdfium2_raw": LIBNAME_GLOBS}
    else:
        sys_name = plat_to_system(pl_name)
        dll_path = ModuleDir_Raw / libname_for_system(sys_name)
        kwargs["package_data"]["pypdfium2_raw"] = (BindingsFN, VersionFN, dll_path.name)
        
        kwargs["distclass"] = BinaryDistribution
        kwargs["cmdclass"]["bdist_wheel"] = bdist_factory(pl_name, dll_path)
        
        if pl_name == ExtPlats.sourcebuild:
            use_tarball_licenses = False
        else:  # pdfium-binaries
            use_tarball_licenses = bool(int( os.getenv("USE_TARBALL_LICENSES", 0) ))
        if use_tarball_licenses:
            license_files.append(f"data/{pl_name}/BUILD_LICENSES/**")
        else:
            license_files.append("BUILD_LICENSES/**")
    
    kwargs["cmdclass"]["build_py"] = buildpy_factory(pl_name, datagen, helpers_info, kwargs["package_data"])
    kwargs["license_files"] = license_files
    
    # An explicit package finder is required for older versions of Python which are stuck with older setuptools (e.g. Python 3.6 has max setuptools 59.6.0).
    # With setuptools >= 61 this could just be omitted entirely thanks to auto-discovery.
    kwargs["packages"] = setuptools.find_packages(where='src', include=["pypdfium2*"], exclude=[])
    
    setuptools.setup(**kwargs)


def _resolve_platname(pl_name):
    if pl_name != ExtPlats.fallback:
        return pl_name
    try:
        system_pdfium._get_pdfium()
    except system_pdfium.PdfiumNotFoundError:
        return ExtPlats.sourcebuild
    else:
        return ExtPlats.system


def main():
    raw_platspec = os.environ.get(PlatSpec_EnvVar, "")
    pl_name, *args = parse_pl_spec(raw_platspec)
    datagen = partial(prepare_setup, pl_name, *args)
    run_setup(_resolve_platname(pl_name), datagen)


if __name__ == "__main__":
    main()
