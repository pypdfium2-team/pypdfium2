<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

Planned Changes
===============

The following API-breaking changes are planned or in consideration:

* Remove `open_pdf()` (replaced by `open_pdf_auto()`).
* Remove `print_toc()` from public support model API.
* In `render_page()` and `render_pdf()`, only accept tuples for the colour argument, not hexadecimal integers.
