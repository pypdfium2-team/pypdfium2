<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Pin ctypesgen in sdist to prevent reoccurrence of {issue}`264` / {issue}`286`. As a drawback, the pin is never committed, so the sdist is not simply reproducible at this time due to dependence on the latest commit hash of the ctypesgen fork at build time.
