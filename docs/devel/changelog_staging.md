<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- In our cibuildwheel workflow, all targets now excercise pypdfium2's test suite. This is implemented as a custom post-cibuildwheel step, using Debian 13 or Alpine 3 containers, respectively. Note, there are known test failures on s390x and musllinux_armv7l (but we still provide builds). In particular, on s390x, opening password-protected PDFs is broken. s390x is "use at own risk"; there is absolutely no warranty.
- Other workflow and cibuildwheel config improvements.
