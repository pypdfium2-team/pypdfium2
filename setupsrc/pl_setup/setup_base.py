# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import shutil
import sysconfig
import setuptools
from glob import glob
from os.path import join, abspath, dirname, basename
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

sys.path.insert(0, dirname(dirname(abspath(__file__))))
from pl_setup.packaging_base import (
    Libnames,
    DataTree,
    ModuleDir,
    VerNamespace,
    PlatformNames,
    clean_artefacts,
)


def _copy_bindings(pl_name):
    
    files = [f for f in glob(join(DataTree, pl_name, '*')) if os.path.isfile(f)]
    assert len(files) == 2
    
    for src_path in files:
        dest_path = join(ModuleDir, basename(src_path))
        shutil.copy(src_path, dest_path)


def _get_linux_tag(arch):
    return "manylinux_2_17_%s.manylinux2014_%s" % (arch, arch)

def _get_musllinux_tag(arch):
    return "musllinux_1_2_%s" % (arch)


def _get_mac_tag(arch, *versions):
    
    assert len(versions) > 0
    
    template = "macosx_%s_%s"
    
    tag = ""
    sep = ""
    for v in versions:
        tag += sep + template % (v, arch)
        sep = "."
    
    return tag


def _get_tag(pl_name):
    # It looks like pip >= 20.3 now accepts macOS wheels with a lower major version than the host system (that is, at least for 10 on 11).
    # Anyway, even if it's fixed now, we definitely still need to support older releases of pip
    # We're intrigued why other major libraries (e. g. pikepdf, pymupdf - both using cibuildwheel) are not doing multi-version tagging for macOS while they still have compatibility tags for manylinux2014.
    if pl_name == PlatformNames.darwin_x64:
        return _get_mac_tag("x86_64", "10_11", "11_0", "12_0")
    elif pl_name == PlatformNames.darwin_arm64:
        return _get_mac_tag("arm64", "11_0", "12_0")
    elif pl_name == PlatformNames.linux_x64:
        return _get_linux_tag("x86_64")
    elif pl_name == PlatformNames.linux_x86:
        return _get_linux_tag("i686")
    elif pl_name == PlatformNames.linux_arm64:
        return _get_linux_tag("aarch64")
    elif pl_name == PlatformNames.linux_arm32:
        return _get_linux_tag("armv7l")
    elif pl_name == PlatformNames.musllinux_x64:
        return _get_musllinux_tag("x86_64")
    elif pl_name == PlatformNames.musllinux_x86:
        return _get_musllinux_tag("i686")
    elif pl_name == PlatformNames.windows_x64:
        return "win_amd64"
    elif pl_name == PlatformNames.windows_arm64:
        return "win_arm64"
    elif pl_name == PlatformNames.windows_x86:
        return "win32"
    elif pl_name == PlatformNames.sourcebuild:
        tag = sysconfig.get_platform()
        for char in ("-", "."):
            tag = tag.replace(char, "_")
        return tag
    else:
        raise ValueError("Unknown platform directory %s" % pl_name)


def _get_bdist(pl_name):
    
    class bdist (_bdist_wheel):
        
        def finalize_options(self, *args, **kws):
            _bdist_wheel.finalize_options(self, *args, **kws)
            self.plat_name_supplied = True
            self.root_is_pure = False
        
        def get_tag(self, *args, **kws):
            return "py3", "none", _get_tag(pl_name)
    
    return bdist


SetupKws = dict(
    version = VerNamespace["V_PYPDFIUM2"],
)


def mkwheel(pl_name):
    
    clean_artefacts()
    _copy_bindings(pl_name)
    
    setuptools.setup(
        package_data = {"": Libnames},
        cmdclass = {"bdist_wheel": _get_bdist(pl_name)},
        **SetupKws,
    )
