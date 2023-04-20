<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `PdfTextPage.get_rect()`: Added missing return code check and updated docs regarding dependence on `count_rects()`.
  Fixed related test code that was broken but disabled by accident (missing asserts). Thanks to Guy Rosin for reporting {issue}`207`.
