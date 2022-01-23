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


TestDir = dirname(abspath(__file__))
ResourceDir = join(TestDir,'resources')
OutputDir = join(TestDir,'output')

class TestFiles:
    render = join(ResourceDir,'render.pdf')
    encrypted = join(ResourceDir,'encrypted.pdf')
    multipage = join(ResourceDir,'multipage.pdf')
    bookmarks = join(ResourceDir,'bookmarks.pdf')
    bookmarks_circular = join(ResourceDir,'bookmarks_circular.pdf')
    cropbox = join(ResourceDir,'cropbox.pdf')
    mediabox_missing = join(ResourceDir,'mediabox_missing.pdf')


def test_paths():
    
    print(ResourceDir)
    assert isdir(ResourceDir)
    
    for attr_name in dir(TestFiles):
        if not attr_name.startswith('_'):
            filepath = getattr(TestFiles, attr_name)
            print(filepath)
            assert isfile(filepath)
