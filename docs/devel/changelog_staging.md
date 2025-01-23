<!-- SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

*API changes*
- Rendering / Bitmap
  * Removed `PdfDocument.render()` (see deprecation rationale in v4.25 changelog). Instead, use `PdfPage.render()` with a loop or process pool.
  * Removed `PdfBitmap.get_info()` and `PdfBitmapInfo`, which existed only on behalf of data transfer with `PdfDocument.render()`.
  * `PdfBitmap.to_numpy()`: If the bitmap is single-channel (grayscale), use a 2d shape to avoid needlessly wrapping each pixel value in a list.
  * `PdfBitmap.from_pil()`: Removed `recopy` parameter.
- Pageobjects
  * Renamed `PdfObject.get_pos()` to `.get_bounds()`.
  * Renamed `PdfImage.get_size()` to `.get_px_size()`.
  * `PdfImage.extract()`: Removed `fb_render` option because it does not fit in this API. If the image's rendered bitmap is desired, use `.get_bitmap(render=True)` in the first place.
- Renamed misleading `PdfMatrix.mirror()` parameters `v, h` to `invert_x, invert_y`, as the terms horizontal/vertical flip commonly refer to the transformation applied, not the axis around which is being flipped (i.e. the previous `v` meant flipping around the Y axis, which is vertical, but the resulting transform is inverting the X coordinates and thus actually horizontal). No behavior change if you did not use keyword arguments.
- `PdfDocument.get_toc()`: Replaced `PdfOutlineItem` namedtuple with method-oriented wrapper classes `PdfBookmark` and `PdfDest`, so callers may retrieve only the properties they actually need. This is closer to pdfium's original API and exposes the underlying raw objects. Provides signed count as-is rather than splitting in `n_kids` and `is_closed`. Also distinguishes between `dest is None` and a dest with unknown mode.
- `get_text_range()`: Removed implicit translation of default calls to `get_text_bounded()`, as pdfium reverted `FPDFText_GetText()` to UCS-2, which resolves the allocation concern. However, callers are encouraged to explicitly use `get_text_bounded()` for full Unicode support.
- Removed legacy version flags.

*Improvements and new features*
- Added `PdfPosConv` and `PdfBitmap.get_posconv(page)` helper for bidirectional translation between page and bitmap coordinates.
- Added `PdfObject.get_quad_points()` to get the corner points of an image or text object.
- Exposed `PdfPage.flatten()` (previously semi-private `_flatten()`), after having found out how to correctly use it. Added check and updated docs accordingly.
- With `PdfImage.get_bitmap(render=True)`, added `scale_to_original` option (defaults to True) to temporarily scale the image to its pixel size. Thanks to Lei Zhang for the suggestion.
- Added context manager support to `PdfDocument`, so it can be used in a `with`-statement, because opening from a file path binds a file descriptor (usually on the C side), which should be released explicitly, given OS limits.
- If document loading failed, `err_code` is now assigned to the `PdfiumError` instance so callers may programmatically handle the error subtype.
- In `PdfPage.render()`, added a new option `use_bgra_on_transparency`. If there is page content with transparency, using BGR(x) may slow down PDFium. Therefore, it is recommended to set this option to True if dynamic (page-dependent) pixel format selection is acceptable. Alternatively, you might want to use only BGRA via `force_bitmap_format=pypdfium2.raw.FPDFBitmap_BGRA` (at the cost of occupying more memory compared to BGR).
- In `PdfBitmap.new_*()` methods, avoid use of `.from_raw()`, and instead call the constructor directly, as most parameters are already known on the caller side when creating a bitmap.
- In the rendering CLI, added `--invert-lightness --exclude-images` post-processing options to render with selective lightness inversion. This may be useful to achieve a "dark theme" for light PDFs while preserving different colors, but goes at the cost of performance. (PDFium also provides a color scheme option, but this only allows you to set colors for certain object types, which are then forced on all instances of that type. This may flatten different colors into one, leading to a loss of visual information.)
- Corrected some null pointer checks: we have to use `bool(ptr)` rather than `ptr is None`.
- Improved startup performance by deferring imports of optional dependencies to the point where they are actually needed, to avoid overhead if you do not use them.
- Simplified version classes (no API change expected).

*Setup*
- Experimental Android support added. We are now packaging `android_21_arm64_v8a` wheels. Other Android targets (`armeabi_v7a`, `x86_64`, `x86`) are handled in setup and should implicitly download the binaries, but we don't currently build wheels for these, due to lower relevance (`x86_64` and `x86` are emulators, i.e. only relevant to developers) and uncertainty if supported by PyPI (`armeabi_v7a` and `x86` are not covered by PEP 738's Tier 3 support). Note, platform detection is provided on a best effort basis, but untested. Please report success or failure.

*Project*
- Merged `tests_old/` back into `tests/`.
- Docs: Improved logic when to include the unreleased version warning and upcoming changelog.
- Cleanly split out conda packaging into an own file, and confined it to the `conda/` directory, to avoid polluting the main setup code.

<!-- TODO
See https://github.com/pypdfium2-team/pypdfium2/blob/devel_old/docs/devel/changelog_staging.md
for how to proceed. Note that some things have already been backported, and some rejected.
-->
