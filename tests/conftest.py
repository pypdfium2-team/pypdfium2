# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import logging
import os
from os.path import (
    join,
    dirname,
    abspath,
)


lib_logger = logging.getLogger('pypdfium2')
lib_logger.addHandler(logging.StreamHandler())


TestDir     = dirname(abspath(__file__))
SourceTree  = dirname(TestDir)
ResourceDir = join(TestDir,'resources')
OutputDir   = join(TestDir,'output')


class _test_discovery:
    def __init__(self):
        for entry in os.listdir(ResourceDir):
            filepath = join(ResourceDir, entry)
            if os.path.isfile(filepath):
                setattr(self, os.path.splitext(entry)[0], filepath)

TestFiles = _test_discovery()


def test_paths():
    
    dirs = (TestDir, SourceTree, ResourceDir, OutputDir)
    for dirpath in dirs:
        print(dirpath)
        assert os.path.isdir(dirpath)
    
    for attr_name in dir(TestFiles):
        if not attr_name.startswith('_'):
            filepath = getattr(TestFiles, attr_name)
            print(attr_name.ljust(20), filepath)
            assert os.path.isfile(filepath)
