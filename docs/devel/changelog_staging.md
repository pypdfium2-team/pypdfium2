<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- In setup code, implemented a workaround to sanitize tar archives on extraction, preventing CVE-2007-4559 directory path traversal attacks in case of malicious input.
  Thanks to Kasimir Schulz of Trellix Research.
  *Note that this issue could only be exploited with a malicious release of pdfium-binaries, and that wheels have never been affected. Nonetheless, to be safe, older versions of pypdfium2 should not be installed from source anymore.*
