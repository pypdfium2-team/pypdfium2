# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import logging
from os.path import join, dirname, abspath, isdir, isfile

lib_logger = logging.getLogger("pypdfium2")
lib_logger.addHandler(logging.StreamHandler())
lib_logger.setLevel(logging.DEBUG)

PyVersion = (sys.version_info.major, sys.version_info.minor)

TestDir     = dirname(abspath(__file__))
SourceTree  = dirname(TestDir)
ResourceDir = join(TestDir, "resources")
OutputDir   = join(TestDir, "output")

sys.path.insert(0, join(SourceTree, "setupsrc"))


class TestFiles:
    render        = join(ResourceDir, "render.pdf")
    encrypted     = join(ResourceDir, "encrypted.pdf")
    multipage     = join(ResourceDir, "multipage.pdf")
    toc           = join(ResourceDir, "toc.pdf")
    toc_viewmodes = join(ResourceDir, "toc_viewmodes.pdf")
    toc_maxdepth  = join(ResourceDir, "toc_maxdepth.pdf")
    toc_circular  = join(ResourceDir, "toc_circular.pdf")
    box_fallback  = join(ResourceDir, "box_fallback.pdf")
    text          = join(ResourceDir, "text.pdf")
    empty         = join(ResourceDir, "empty.pdf")
    images        = join(ResourceDir, "images.pdf")
    form          = join(ResourceDir, "form_listbox.pdf")
    mona_lisa     = join(ResourceDir, "mona_lisa.jpg")


ExpRenderPixels = (
    ( (0,   0  ), (255, 255, 255) ),
    ( (150, 180), (129, 212, 26 ) ),
    ( (150, 390), (42,  96,  153) ),
    ( (150, 570), (128, 0,   128) ),
)


def iterate_testfiles(skip_encrypted=True):
    encrypted = (TestFiles.encrypted, )
    for attr_name in dir(TestFiles):
        if attr_name.startswith("_"):
            continue
        member = getattr(TestFiles, attr_name)
        if skip_encrypted and member in encrypted:
            continue
        yield member


def get_members(cls):
    members = []
    for attr in dir(cls):
        if attr.startswith("_"):
            continue
        members.append( getattr(cls, attr) )
    return members


def test_testpaths():
    for dirpath in (TestDir, SourceTree, ResourceDir, OutputDir):
        assert isdir(dirpath)
    for filepath in iterate_testfiles(False):
        assert isfile(filepath)
