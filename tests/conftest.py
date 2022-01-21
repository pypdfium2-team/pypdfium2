# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import logging
from os.path import (
    join,
    isdir,
    isfile,
    dirname,
    abspath,
)


lib_logger = logging.getLogger('pypdfium2')
lib_logger.addHandler(logging.StreamHandler())


TestDir     = dirname(abspath(__file__))
ResourceDir = join(TestDir,'resources')
OutputDir   = join(TestDir,'output')

class TestFiles:
    render    = join(ResourceDir,'test_render.pdf')
    encrypted = join(ResourceDir,'test_encrypted.pdf')
    multipage = join(ResourceDir,'test_multipage.pdf')
    bookmarks = join(ResourceDir,'test_bookmarks.pdf')
    bookmarks_circular = join(ResourceDir,'test_bookmarks_circular.pdf')


def test_paths():
    
    print(ResourceDir)
    assert isdir(ResourceDir)
    
    for attr_name in dir(TestFiles):
        if not attr_name.startswith('_'):
            filepath = getattr(TestFiles, attr_name)
            print(filepath)
            assert isfile(filepath)
