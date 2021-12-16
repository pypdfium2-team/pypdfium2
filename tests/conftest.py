# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import pytest
from pathlib import Path


TestDir     = Path(__file__).parent.resolve()
ResourceDir = TestDir / 'resources'
OutputDir   = TestDir / 'output'

class TestFiles:
    render    = ResourceDir / 'test_render.pdf'
    encrypted = ResourceDir / 'test_encrypted.pdf'
    multipage = ResourceDir / 'test_multipage.pdf'
    bookmarks = ResourceDir / 'test_bookmarks.pdf'
    bookmarks_circular = ResourceDir / 'test_bookmarks_circular.pdf'


def test_paths():
    
    print(ResourceDir)
    assert ResourceDir.is_dir()
    
    for attr_name in dir(TestFiles):
        if not attr_name.startswith('_'):
            file = getattr(TestFiles, attr_name)
            print(file)
            assert file.exists()
