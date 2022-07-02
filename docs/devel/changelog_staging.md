<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Changelog for next release

- Improved changelog integration of automatic releases.
- Disabled implicit source build in `setup.py`, which used to be the fallback if no pre-built binaries
  are available for the host platform. Now, an exception is raised instead.
- Subtle improvements were applied to the handling of input buffers (providing `read()` beside `readinto()` is now explicitly required).
- Concerning file access, the autoclose logic has been moved from the loder data holder to `PdfDocument.close()`, which is somewhat more obvious.
- In the release workflow, reverted an inelegant change regarding dependency installation order.
- Updated hosts for release workflow and documentation build to Python 3.10.
