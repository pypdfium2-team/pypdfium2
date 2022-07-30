<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Changelog for next release

- Added a new option `rm_security` to `PdfDocument.save()`.
- Added support for password-protected PDFs in the CLI subcommands `merge`, `render`, `tile` and `toc`.
- Corrected the release workflow to avoid incrementing minor version twice.
- The stable branch is now always updated, even if it contains commits that are not in main.
- Various code style improvements.
