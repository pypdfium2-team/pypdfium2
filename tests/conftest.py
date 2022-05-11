# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import logging
from os.path import join, dirname, abspath

lib_logger = logging.getLogger('pypdfium2')
lib_logger.addHandler(logging.StreamHandler())

TestDir     = dirname(abspath(__file__))
SourceTree  = dirname(TestDir)
ResourceDir = join(TestDir,'resources')
OutputDir   = join(TestDir,'output')

sys.path.insert(0, join(SourceTree,'setupsrc'))
from pl_setup.packaging_base import PlatformNames


class TestFiles:
    render             = join(ResourceDir,'render.pdf')
    encrypted          = join(ResourceDir,'encrypted.pdf')
    multipage          = join(ResourceDir,'multipage.pdf')
    bookmarks          = join(ResourceDir,'bookmarks.pdf')
    bookmarks_circular = join(ResourceDir,'bookmarks_circular.pdf')
    boxes              = join(ResourceDir,'boxes.pdf')


def iterate_testfiles(skip_encrypted=True):
    encrypted = (TestFiles.encrypted, )
    for attr_name in dir(TestFiles):
        if attr_name.startswith('_'):
            continue
        member = getattr(TestFiles, attr_name)
        if skip_encrypted and member in encrypted:
            continue
        yield member


def get_members(cls):
    members = []
    for attr in dir(cls):
        if attr.startswith('_'):
            continue
        members.append(attr)
    return members


pl_names = get_members(PlatformNames)
