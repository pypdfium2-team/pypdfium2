# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import pytest
from pathlib import Path


ResourceDir = Path(__file__).parent.resolve() / 'resources'

class TestFiles:
    test_render = ResourceDir / 'test_render.pdf'


def test_paths():
    
    print(ResourceDir)
    assert ResourceDir.is_dir()
    
    for attr_name in dir(TestFiles):
        if not attr_name.startswith('_'):
            file = getattr(TestFiles, attr_name)
            print(file)
            assert file.exists()


if __name__ == '__main__':
    test_paths()
