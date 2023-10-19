# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
from pathlib import Path
# import pypdfium2.__main__ as pdfium_cli

# if tests/ and tests_old/ are run together as usual, this would initialize logging twice
# pdfium_cli.setup_logging()

PyVersion = (sys.version_info.major, sys.version_info.minor)

TestDir     = Path(__file__).absolute().parent
ProjectDir  = TestDir.parent
ResourceDir = TestDir / "resources"
OutputDir   = TestDir / "output"

sys.path.insert(0, str(ProjectDir / "setupsrc"))


class TestFiles:
    render        = ResourceDir / "render.pdf"
    encrypted     = ResourceDir / "encrypted.pdf"
    multipage     = ResourceDir / "multipage.pdf"
    toc           = ResourceDir / "toc.pdf"
    toc_viewmodes = ResourceDir / "toc_viewmodes.pdf"
    toc_maxdepth  = ResourceDir / "toc_maxdepth.pdf"
    toc_circular  = ResourceDir / "toc_circular.pdf"
    box_fallback  = ResourceDir / "box_fallback.pdf"
    text          = ResourceDir / "text.pdf"
    empty         = ResourceDir / "empty.pdf"
    images        = ResourceDir / "images.pdf"
    form          = ResourceDir / "forms.pdf"
    attachments   = ResourceDir / "attachments.pdf"
    mona_lisa     = ResourceDir / "mona_lisa.jpg"


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
    for dirpath in (TestDir, ProjectDir, ResourceDir, OutputDir):
        assert dirpath.is_dir()
    for filepath in iterate_testfiles(False):
        assert filepath.is_file()
