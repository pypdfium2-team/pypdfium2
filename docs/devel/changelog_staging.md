<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Changelog for next release

- Switched from `FPDF_LoadMemDocument()` to `FPDF_LoadMemDocument64()`. The latter uses `size_t` rather than `int` to avoid integer overflows on huge files.
- Pinned `ctypesgen` to a more recent stable commit in `pyproject.toml`, as the release is fairly outdated. Suggested pinning of `wheel` by code comment.
- Updated planned changes.
