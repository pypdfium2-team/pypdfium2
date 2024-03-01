<!-- SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `get_text_range()`: Fixed a buffer size regression introduced in v4.26.0, caused by an unexpected behavior change in pdfium (thanks @elonzh for the bug report, {issue}`298`). Since that change, it is not possible anymore to tell the exact amount of memory needed, so we have to allocate for the worst case. Therefore, while this problem persists, it is recommended to instead use `get_text_bounded()` where possible.
