<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Contributing

Contributions and improvements to PyPDFium2 are very welcome. Here are a few instructions to help you
with your contribution, and some rules that we would like you to follow:

* PyPDFium2 adheres to the [SPDX standard][spdx-licenses] for license and copyright headers.
  If you create new files, please always add such a header. For binary files, you may add a
  corresponding section in [`.reuse/dep5`][dep5] (this is equivalent to a Debian copyright file).
  If you edit an existing file, please add your name and the current year to its copyright header,
  especially for larger work (i. e. more than 10 lines or particularly complex code).
  You can ensure standard compliance using [`reuse lint`][reuse-lint].
* Please always use spaces instead of tabs. You'll want to configure your editor to automatically
  replace a tab with four spaces.
  *Background*: Python code is formatted by indentation. If different indentation patterns are mixed
  in an inconsistent way, the Python interpreter will not be able to parse your code.
* Blank lines should contain as many spaces that they stay on the correct indentation level.
  This makes editing a lot easier. (VS Code: Uncheck "Editor: Trim Auto Whitespace")
* Files should always end with a newline character for consistency.
  (VS Code: Check "Files: Insert Final Newline")
* Type hints and code comments are appreciated wherever they improve readability.
* Please try to keep compatibility with the minimum supported Python version defined in
  [`setup.cfg`][setup-cfg]. This means to avoid newer features like f-strings or keywords-only
  enforcement.
* For working with file paths, we prefer to use `os.path` / `shutil` / `glob` instead of `pathlib`.
* In the module itself, no relative imports must be used. Absolute imports are preferable.
  Outside the `src/` directory, realative imports are allowed, though.

[spdx-licenses]: https://spdx.org/licenses/
[reuse-lint]: https://pypi.org/project/reuse/
[dep5]: ../../.reuse/dep5
[setup-cfg]: ../../setup.cfg
