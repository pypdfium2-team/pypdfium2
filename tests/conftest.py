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


class TestFiles:
    render = join(ResourceDir,'render.pdf')
    encrypted = join(ResourceDir,'encrypted.pdf')
    multipage = join(ResourceDir,'multipage.pdf')
    bookmarks = join(ResourceDir,'bookmarks.pdf')
    bookmarks_circular = join(ResourceDir,'bookmarks_circular.pdf')
    cropbox = join(ResourceDir,'cropbox.pdf')
    mediabox_missing = join(ResourceDir,'mediabox_missing.pdf')
    nonascii = join(ResourceDir,'nonascii_tênfilechứakýtựéèáàçß 发短信.pdf')


def iterate_testfiles(skip_encrypted=True):
    
    encrypted = (TestFiles.encrypted, )
    
    for attr_name in dir(TestFiles):
        
        if attr_name.startswith('_'):
            continue
        
        member = getattr(TestFiles, attr_name)
        if skip_encrypted and member in encrypted:
            continue
        
        yield member


def test_paths():
    
    dirs = (TestDir, SourceTree, ResourceDir, OutputDir)
    for dirpath in dirs:
        print(dirpath)
        assert os.path.isdir(dirpath)
    
    for filepath in iterate_testfiles(False):
        print(filepath)
        assert os.path.isfile(filepath)
