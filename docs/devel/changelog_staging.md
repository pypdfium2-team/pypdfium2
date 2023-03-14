<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- On multi-page rendering, `PdfDocument` objects constructed in parallel jobs now correctly initialize a form env if the triggering `PdfDocument` has an active one. (In versions 4.1 and 4.2, a form env would never be initialized and thus forms never rendered. In v4.0, a form env would always be initialized for documents with forms.)
- API-breaking change on `PdfDocument.init_forms()`: `config` (`FPDF_FORMFILLINFO`) parameter changed to `config_maker` (`Callable` -> `FPDF_FORMFILLINFO`), on behalf of the multi-page renderer.
