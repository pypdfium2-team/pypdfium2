<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Disruption: `PdfPage.insert_text()` does not generate page content automatically anymore. The new `PdfPage.generate_content()` method now needs to be called to apply changes, to avoid generating content repeatedly.
