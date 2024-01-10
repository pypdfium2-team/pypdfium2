# SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
from pathlib import Path
from argparse import Namespace
import pypdfium2.__main__ as pdfium_cli


pdfium_cli.setup_logging()

TestDir         = Path(__file__).parent
ProjectDir      = TestDir.parent
ResourceDir     = TestDir / "resources"
OutputDir       = TestDir / "output"
ExpectationsDir = TestDir / "expectations"

# Add setup helper module so we can import it in the test suite
sys.path.insert(0, str(ProjectDir / "setupsrc"))


def _gather_resources(dir, skip_exts=[".in"]):
    test_files = Namespace()
    for path in dir.iterdir():
        if not path.is_file() or path.suffix in skip_exts:
            continue
        setattr(test_files, path.stem, (dir / path.name))
    return test_files


TestResources = _gather_resources(ResourceDir)
TestExpectations = _gather_resources(ExpectationsDir)
