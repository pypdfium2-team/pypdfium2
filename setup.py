# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# See also https://stackoverflow.com/questions/45150304/how-to-force-a-python-wheel-to-be-platform-specific-when-building-it and https://github.com/innodatalabs/redstork/blob/master/setup.py

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

class BinaryDistribution (setuptools.Distribution):
    
    def has_ext_modules(self):
        return True


def buildpy_factory(pl_name, modnames, datagen, helpers_info, package_data):
    
    # https://cibuildwheel.pypa.io/en/stable/faq/#actions-you-need-to-perform-before-building
    
    class pypdfium_buildpy (buildpy_orig):
        
        def run(self, *args, **kwargs):
            
            if ModuleRaw in modnames and pl_name != ExtPlats.sdist:
                datagen()
                assert_exists(ModuleDir_Raw, package_data["pypdfium2_raw"])
            
            if ModuleHelpers in modnames:
                helpers_info["is_editable"] = bool(self.editable_mode)
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


def _get_fixed_helpers_info(pl_name):
    
    helpers_info = get_helpers_info()
    if pl_name != ExtPlats.sdist:
        return helpers_info
    
    if helpers_info["dirty"]:
        # ignore dirty state due to craft.py::tmp_ctypesgen_pin()
        if int(os.environ.get("SDIST_IGNORE_DIRTY", 0)):
            helpers_info["dirty"] = False
    else:
        log("Warning: sdist without ctypesgen pin, or git describe not working?")
    
    return helpers_info


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

BASE_PLATFILES = (BindingsFN, VersionFN)


def run_setup(modnames, pl_name, datagen):
    
    # FIXME ambiguity between `pl_name == ExtPlats.sdist` and `ModuleRaw not in modnames` ?
    
    kwargs = dict(
        name = "pypdfium2",
        description = "Python bindings to PDFium",
        license = "BSD-3-Clause, Apache-2.0, dependency licenses",
        # TODO Fix and re-enable Python >= 3.6 (see the note in src/pypdfium2/_lazy.py for why it is broken)
        python_requires = ">= 3.8",
        cmdclass = {},
        package_dir = {},
        package_data = {},
    )
    
    platfiles = []
    dll_path = None
    if pl_name != ExtPlats.sdist:
        platfiles += BASE_PLATFILES
        if pl_name != ExtPlats.system:
            sys_name = plat_to_system(pl_name)
            dll_path = ModuleDir_Raw / libname_for_system(sys_name)
            platfiles.append(dll_path.name)
    
    license_files = list(LICENSES_SHARED)
    if pl_name == ExtPlats.sdist:
        license_files.extend(LICENSES_SDIST)
    
    if modnames == [ModuleHelpers]:
        kwargs["name"] += "_helpers"
        kwargs["description"] += " (helpers module)"
        kwargs["install_requires"] = ["pypdfium2_raw"]
    elif modnames == [ModuleRaw]:
        kwargs["name"] += "_raw"
        kwargs["description"] += " (raw module)"
        # FIXME Requires pre-generated version file. This is since 5.10, when datagen was deferred into build_py.
        log(f"Warning: PYPDFIUM_MODULES=raw expects pre-generated version file at src/pypdfium2_raw/{VersionFN}. Callers must ensure this matches the version being built!")
        pdfium_fullver, _ = read_pdfium_info(ModuleDir_Raw)
        kwargs["version"] = str(pdfium_fullver)
    else:
        assert any(m in modnames for m in (ModuleHelpers, ModuleRaw)), \
               f"At least one core module is required. Check {ModulesSpec_EnvVar}."
    
    helpers_info = None
    if ModuleHelpers in modnames:
        helpers_info = _get_fixed_helpers_info(pl_name)
        kwargs["version"] = merge_tag(helpers_info, mode="py")
        kwargs["package_dir"]["pypdfium2"] = "src/pypdfium2"
        kwargs["package_dir"]["pypdfium2_cli"] = "src/pypdfium2_cli"
        kwargs["package_dir"]["pypdfium2_cfg"] = "src/pypdfium2_cfg"
        kwargs["package_data"]["pypdfium2"] = (VersionFN, )
        kwargs["entry_points"] = dict(console_scripts=["pypdfium2 = pypdfium2_cli.__main__:cli_main"])
    if ModuleRaw in modnames:
        kwargs["package_dir"]["pypdfium2_raw"] = "src/pypdfium2_raw"
        if platfiles:
            kwargs["package_data"]["pypdfium2_raw"] = platfiles
    
    if ModuleRaw not in modnames or pl_name == ExtPlats.sdist:
        kwargs["exclude_package_data"] = {"pypdfium2_raw": (*BASE_PLATFILES, *LIBNAME_GLOBS)}
    elif pl_name == ExtPlats.system:
        kwargs["exclude_package_data"] = {"pypdfium2_raw": LIBNAME_GLOBS}
    else:
        
        if pl_name == ExtPlats.sourcebuild:
            use_tarball_licenses = False
        else:  # pdfium-binaries
            use_tarball_licenses = bool(int( os.getenv("USE_TARBALL_LICENSES", 0) ))
        
        if use_tarball_licenses:
            license_files.append(f"data/{pl_name}/BUILD_LICENSES/**")
        else:
            license_files.append("BUILD_LICENSES/**")
        
        kwargs["distclass"] = BinaryDistribution
        kwargs["cmdclass"]["bdist_wheel"] = bdist_factory(pl_name, dll_path)
    
    kwargs["cmdclass"]["build_py"] = buildpy_factory(pl_name, modnames, datagen, helpers_info, kwargs["package_data"])
    kwargs["license_files"] = license_files
    
    setuptools.setup(**kwargs)


def _parse_modspec(modspec):
    if modspec:
        modnames = modspec.split(",")
        assert set(modnames).issubset(ModulesAll)
        assert len(modnames) in (1, 2)
    else:
        modnames = ModulesAll
    return modnames

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
    
    raw_modspec = os.environ.get(ModulesSpec_EnvVar, "")
    raw_platspec = os.environ.get(PlatSpec_EnvVar, "")
    
    modnames = _parse_modspec(raw_modspec)
    pl_name, *args = parse_pl_spec(raw_platspec)
    if pl_name == ExtPlats.sdist and modnames != ModulesAll:
        raise ValueError(f"Partial sdist does not make sense - unset {ModulesSpec_EnvVar}.")
    
    datagen = partial(prepare_setup, pl_name, *args)
    run_setup(modnames, _resolve_platname(pl_name), datagen)


if __name__ == "__main__":
    main()
