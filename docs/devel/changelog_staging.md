<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

- Prevent wheel content from wrongly being placed in a `purelib` folder by explicitly declaring
  that pypdfium2 ships with a binary extension. This is relevant for some systems to separate
  platform-dependant packages from pure-python packages (i. e. `/usr/lib64` instead of `/usr/lib`).
  Confer PEP 427.
- Added a new function `PdfDocument.get_version()` to obtain the PDF version of a document.
