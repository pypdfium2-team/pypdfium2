<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Disruption: `PdfPage.insert_text()` does not generate page content automatically anymore. The new `PdfPage.generate_content()` method now needs to be called to apply changes, to avoid generating content repeatedly.
- Added a helper class for transform matrices.
- Added support models to capture pages as XObjects, to get page objects for XObjects, to transform them with matrices, and to insert page objects into a page. This may be used to implement a custom N-up compositor, for instance.
