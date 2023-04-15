<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Planned Changes

<!-- Currently, no API breaking changes are planned. -->

```{note}
You may search for `TODO(v5)` to find the code spots in question.
```

The following API breaking changes are in consideration for the next major release:

- The `PdfDocument.get_toc()` / `PdfOutlineItem` API will be changed.
  * The parameters `is_closed` (bool) and `n_kids` (abs int) will be replaced by `count` (int),
    where the state corresponds to the value's sign.
  * Instead of loading bookmark info into namedtuples in a predefined fashion, a wrapper
    around the raw pdfium object with on-demand properties shall be returned.
