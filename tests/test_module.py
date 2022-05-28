# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import configparser
from os.path import join, isdir, isfile
from .conftest import *


def test_testpaths():
    for dirpath in (TestDir, SourceTree, ResourceDir, OutputDir):
        assert isdir(dirpath)
    for filepath in iterate_testfiles(False):
        assert isfile(filepath)


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
