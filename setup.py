# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# See also https://stackoverflow.com/questions/45150304/how-to-force-a-python-wheel-to-be-platform-specific-when-building-it and https://github.com/innodatalabs/redstork/blob/master/setup.py

import os
import sys
from pathlib import Path
import setuptools
from setuptools.command.build_py import build_py as build_py_orig
try:
    from setuptools.command.bdist_wheel import bdist_wheel
except ImportError:
    from wheel.bdist_wheel import bdist_wheel

sys.path.insert(0, str(Path(__file__).parent/"setupsrc"))
from base import *
from emplace import prepare_setup


# Use a custom distclass declaring we have a binary extension, to prevent modules from being nested in a purelib/ subdirectory in wheels.
# This will also set `Root-Is-Purelib: false` in the WHEEL file, and make the wheel tag platform specific by default.

class BinaryDistribution (setuptools.Distribution):
    
    def has_ext_modules(self):
        return True


def bdist_factory(pl_name):
    
    class pypdfium_bdist (bdist_wheel):
        
        def finalize_options(self, *args, **kws):
            bdist_wheel.finalize_options(self, *args, **kws)
            # should be handled by the distclass already, but set it again to be on the safe side
            self.root_is_pure = False
        
        def get_tag(self, *args, **kws):
            if pl_name == ExtPlats.sourcebuild:
                # In case of cross-compilation (or even just proper packaging), the caller needs to set the tag.
                plat_tag = os.environ.get("CROSS_TAG")
                # Otherwise, forward the host's tag as given by bdist_wheel.
                # Alternatively, the sourcebuild clause in base.py::get_wheel_tag() should be roughly equivalent.
                # The underlying API being wrapped is sysconfig.get_platform().
                if not plat_tag:
                    _py, _abi, plat_tag = bdist_wheel.get_tag(self, *args, **kws)
            else:
                plat_tag = get_wheel_tag(pl_name)
            return "py3", "none", plat_tag
    
    return pypdfium_bdist


class pypdfium_build_py (build_py_orig):
        
    def run(self, *args, **kwargs):
        if hasattr(self, "editable_mode"):
            helpers_info = read_json(ModuleDir_Helpers/VersionFN)
            helpers_info["is_editable"] = bool(self.editable_mode)
            write_json(ModuleDir_Helpers/VersionFN, helpers_info)
        else:
            log("!!! Warning: cmdclass does not provide `editable_mode` attribute.")
        build_py_orig.run(self, *args, **kwargs)


LICENSES_SHARED = (
    "LICENSES/Apache-2.0.txt",
    "LICENSES/BSD-3-Clause.txt",
    "LICENSES/CC-BY-4.0.txt",
)
LICENSES_SDIST = (
    # our sdists don't currently include tests, so we don't need to list the other licenses here
    "REUSE.toml",
)


def assert_exists(dir, data_files):
    missing = tuple(f for f in data_files if not (dir/f).exists())
    if missing:
        assert False, f"Missing data files: {missing}"


def run_setup(modnames, pl_name, platfiles):
    
    # FIXME ambiguity between `pl_name == ExtPlats.sdist` and `ModuleRaw not in modnames` ?
    
    kwargs = dict(
        name = "pypdfium2",
        description = "Python bindings to PDFium",
        license = "BSD-3-Clause, Apache-2.0, dependency licenses",
        python_requires = ">= 3.6",
        cmdclass = {},
        package_dir = {},
        package_data = {},
        install_requires = [],
    )
    
    license_files = list(LICENSES_SHARED)
    if pl_name == ExtPlats.sdist:
        license_files.extend(LICENSES_SDIST)
    
    if modnames == [ModuleHelpers]:
        kwargs["name"] += "_helpers"
        kwargs["description"] += " (helpers module)"
        kwargs["install_requires"].append("pypdfium2_raw")
    elif modnames == [ModuleRaw]:
        kwargs["name"] += "_raw"
        kwargs["description"] += " (raw module)"
        pdfium_fullver, _ = read_pdfium_info(ModuleDir_Raw)
        kwargs["version"] = str(pdfium_fullver)
    else:
        assert any(m in modnames for m in (ModuleHelpers, ModuleRaw)), \
               f"At least one core module is required. Check {ModulesSpec_EnvVar}."
    
    if ModuleHelpers in modnames:
        helpers_info = get_helpers_info()
        if pl_name == ExtPlats.sdist:
            if helpers_info["dirty"]:
                # ignore dirty state due to craft.py::tmp_ctypesgen_pin()
                if int(os.environ.get("SDIST_IGNORE_DIRTY", 0)):
                    helpers_info["dirty"] = False
            else:
                log("Warning: sdist without ctypesgen pin, or git describe not working?")
        kwargs["version"] = merge_tag(helpers_info, mode="py")
        # is_editable = None: unknown/fallback in case the cmdclass is not reached
        helpers_info["is_editable"] = None
        write_json(ModuleDir_Helpers/VersionFN, helpers_info)
        kwargs["cmdclass"]["build_py"] = pypdfium_build_py
        kwargs["package_dir"]["pypdfium2"] = "src/pypdfium2"
        kwargs["package_data"]["pypdfium2"] = (VersionFN, )
        kwargs["entry_points"] = dict(console_scripts=["pypdfium2 = pypdfium2.__main__:cli_main"])
    if ModuleRaw in modnames:
        kwargs["package_dir"]["pypdfium2_raw"] = "src/pypdfium2_raw"
        if platfiles:
            kwargs["package_data"]["pypdfium2_raw"] = platfiles
    
    if ModuleRaw not in modnames or pl_name == ExtPlats.sdist:
        kwargs["exclude_package_data"] = {"pypdfium2_raw": (VersionFN, BindingsFN, *LIBNAME_GLOBS)}
    elif pl_name == ExtPlats.system:
        kwargs["exclude_package_data"] = {"pypdfium2_raw": LIBNAME_GLOBS}
    else:
        if pl_name == ExtPlats.sourcebuild:
            license_files.append("BUILD_LICENSES/**")
        else:
            # FIXME This gives a deeply nested directory structure.
            # The author is not aware of a way to achieve a more flat structure with setuptools.
            license_files.append(f"data/{pl_name}/BUILD_LICENSES/**")
        kwargs["distclass"] = BinaryDistribution
        kwargs["cmdclass"]["bdist_wheel"] = bdist_factory(pl_name)
    
    kwargs["license_files"] = license_files
    
    # check
    if "pypdfium2" in kwargs["package_data"]:
        assert_exists(ModuleDir_Helpers, kwargs["package_data"]["pypdfium2"])
    if "pypdfium2_raw" in kwargs["package_data"]:
        assert_exists(ModuleDir_Raw, kwargs["package_data"]["pypdfium2_raw"])
    
    setuptools.setup(**kwargs)


def main():
    
    raw_modspec = os.environ.get(ModulesSpec_EnvVar, "")
    raw_platspec = os.environ.get(PlatSpec_EnvVar, "")
    
    modnames = parse_modspec(raw_modspec)
    pl_name, sub_target, requested_ver, flags = parse_pl_spec(raw_platspec)
    
    if pl_name == ExtPlats.sdist and modnames != ModulesAll:
        raise ValueError(f"Partial sdist does not make sense - unset {ModulesSpec_EnvVar}.")
    
    if ModuleRaw in modnames and pl_name != ExtPlats.sdist:
        platfiles, pl_name = prepare_setup(pl_name, sub_target, requested_ver, flags)
    else:
        platfiles = ()
    
    run_setup(modnames, pl_name, platfiles)


if __name__ == "__main__":
    main()
