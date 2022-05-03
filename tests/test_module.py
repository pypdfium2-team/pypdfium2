# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import configparser
import pkg_resources
from os.path import join, isdir, isfile
from pypdfium2 import V_PYPDFIUM2, V_LIBPDFIUM
from .conftest import *


def test_testpaths():
    for dirpath in (TestDir, SourceTree, ResourceDir, OutputDir):
        assert isdir(dirpath)
    for filepath in iterate_testfiles(False):
        assert isfile(filepath)


def test_versions():
    assert V_PYPDFIUM2 == pkg_resources.get_distribution('pypdfium2').version
    assert V_LIBPDFIUM > 5000 


def test_entrypoint():    
    
    setup_cfg = configparser.ConfigParser()
    setup_cfg.read( join(SourceTree,'setup.cfg') )
    console_scripts = setup_cfg['options.entry_points']['console_scripts']
    
    entry_point = console_scripts.split('=')[-1].strip().split(':')
    module_path = entry_point[0]
    method_name = entry_point[1]
    
    namespace = {}
    exec("from %s import %s" % (module_path, method_name), namespace)
    assert method_name in namespace
    
    function = namespace[method_name]
    assert callable(function)
