<!-- SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

*API changes*
- Rendering / Bitmap
  * Removed `PdfDocument.render()` (see deprecation rationale in v4.25 changelog). Instead, use `PdfPage.render()` with a loop or process pool.
  * Removed `PdfBitmap.get_info()` and `PdfBitmapInfo`, which existed mainly on behalf of data transfer with `PdfDocument.render()`. Instead, take the info from the `PdfBitmap` object directly. (If using an adapter that copies, you may want to store the relevant info in variables to avoid holding a reference to the original buffer.)
  * `PdfBitmap.fill_rect()`: Changed argument order. The `color` parameter now goes first.
  * `PdfBitmap.to_numpy()`: If the bitmap is single-channel (grayscale), use a 2d shape to avoid needlessly wrapping each pixel value in a list.
  * `PdfBitmap.from_pil()`: Removed `recopy` parameter.
- Pageobjects
  * Renamed `PdfObject.get_pos()` to `.get_bounds()`.
  * Renamed `PdfImage.get_size()` to `.get_px_size()`.
  * `PdfImage.extract()`: Removed `fb_render` option because it does not fit in this API. If the image's rendered bitmap is desired, use `.get_bitmap(render=True)` in the first place.
- `PdfDocument.get_toc()`: Replaced `PdfOutlineItem` namedtuple with method-oriented wrapper classes `PdfBookmark` and `PdfDest`, so callers may retrieve only the properties they actually need. This is closer to pdfium's original API and exposes the underlying raw objects. Provides signed count as-is rather than splitting in `n_kids` and `is_closed`. Also distinguishes between `dest is None` and a dest with unknown mode.
- Renamed misleading `PdfMatrix.mirror()` parameters `v, h` to `invert_x, invert_y`, as the terms horizontal/vertical flip commonly refer to the transformation applied, not the axis around which is being flipped (i.e. the previous `v` meant flipping around the Y axis, which is vertical, but the resulting transform is inverting the X coordinates and thus actually horizontal). No behavior change if you did not use keyword arguments.
- `PdfTextPage.get_text_range()`: Removed implicit translation of default calls to `.get_text_bounded()`, as pdfium reverted `FPDFText_GetText()` to UCS-2, which resolves the allocation concern. However, callers are encouraged to explicitly use `.get_text_bounded()` for full Unicode support.
- Removed legacy version flags `V_PYPDFIUM2, V_LIBPDFIUM, V_BUILDNAME, V_PDFIUM_IS_V8, V_LIBPDFIUM_FULL` in favor of `PYPDFIUM_INFO, PDFIUM_INFO`.

*Improvements and new features*
- Added `PdfPosConv` and `PdfBitmap.get_posconv(page)` helper for bidirectional translation between page and bitmap coordinates.
- Added `PdfObject.get_quad_points()` to get the corner points of an image or text object.
- Exposed `PdfPage.flatten()` (previously semi-private `_flatten()`), after having found out how to correctly use it. Added check and updated docs accordingly.
- With `PdfImage.get_bitmap(render=True)`, added `scale_to_original` option (defaults to True) to temporarily scale the image to its native pixel size. This should improve output quality and make the API substantially more useful. Thanks to Lei Zhang for the suggestion.
- Added context manager support to `PdfDocument`, so it can be used in a `with`-statement, because opening from a file path binds a file descriptor (usually on the C side), which should be released explicitly, given OS limits.
- If document loading failed, `err_code` is now assigned to the `PdfiumError` instance so callers may programmatically handle the error subtype. This addresses {issue}`308`.
- In `PdfPage.render()`, added a new option `use_bgra_on_transparency`. If there is page content with transparency, using BGR(x) may slow down PDFium. Therefore, it is recommended to set this option to True if dynamic (page-dependent) pixel format selection is acceptable. Alternatively, you might want to use only BGRA via `force_bitmap_format=pypdfium2.raw.FPDFBitmap_BGRA` (at the cost of occupying more memory compared to BGR).
- In `PdfBitmap.new_*()` methods, avoid use of `.from_raw()`, and instead call the constructor directly, as most parameters are already known on the caller side when creating a bitmap.
- `PdfPage.remove_obj()` is now aware of objects nested in Form XObjects, and will use the new pdfium API `FPDFFormObj_RemoveObject()` in that case. Correspondingly, a `.container` attribute has been added to `PdfObject`, which points to the parent Form XObject, or None if the object is not nested.
- In the rendering CLI, added `--invert-lightness --exclude-images` post-processing options to render with selective lightness inversion. This may be useful to achieve a "dark theme" for light PDFs while preserving different colors, but goes at the cost of performance. (PDFium also provides a color scheme option, but this only allows you to set colors for certain object types, which are then forced on all instances of the type in question. This may flatten different colors into one, leading to a loss of visual information.)
- Corrected some null pointer checks: we have to use `bool(ptr)` rather than `ptr is None`.
- In `PdfDocument.save()`, changed default of `flags` from `FPDF_NO_INCREMENTAL` to `0`, as suggested by an upstream maintainer.
- Avoid creation of sized pointer types at runtime, to not blow up an unbounded pointer type cache of ctypes, which could effectively lead to a memory leak in a long-running application (i.e. do `(type * size).from_address(addressof(first_ptr.contents))` instead of `cast(first_ptr, POINTER(type * size)).contents`). Thanks to Richard Hundt for the bug report, {issue}`346`. The root issue (ctypes using an unbounded cache in the first place) has been fixed recently in Python `3.14`. See below for a list of APIs that were affected:
  * Anything using `_buffer_reader`/`_buffer_writer` under the hood (`PdfDocument` created from byte stream input, `PdfImage.load_jpeg()`, `PdfDocument.save()`).
  * `PdfBitmap.from_raw()` rsp. `PdfBitmap._get_buffer()` and their internal callers (`PdfBitmap` makers `new_foreign` and `new_foreign_simple`, `PdfImage.get_bitmap()`).
  * Also, some Readme snippets were affected, including the raw API rendering example. The Readme has been updated to mention the problem and use `.from_address(...)` instead.
  * *With older versions of pypdfium2/python, periodically calling `ctypes._reset_cache()` can work around this issue.*
- Improved startup performance by deferring imports of optional dependencies to the point where they are actually needed, to avoid overhead if you do not use them.
- Simplified version classes (no API change expected).

*Platforms*
- __Experimental__ Android (PEP 738) and iOS (PEP 730) support added.
  Android `arm64_v8a`, `armeabi_v7a`, `x86_64`, `x86` and iOS `arm64` device and `arm64`, `x86_64` simulators are now handled in setup and should implicitly download the right pdfium-binaries. Provided on a best effort basis, and largely untested. Testers/feedback welcome.
- pypdfium2's setup is now also capable of producing wheels for these platforms, but they will not actually be included in releases at this time. (Once Termux ships Python 3.13, we may want to publish Android `arm64_v8a` and maybe `armeabi_v7a` wheels, but we do not intend to provide wheels for simulators.)
- iOS will not actually work yet, as the PEP indicates binaries ought to be moved to a special Frameworks location for permission reasons, in which case you'd also have to patch pypdfium2's library search. We cannot do anything about this yet without access to a device or clearer instructions. Community help would be appreciated here.

*Setup*
- When pdfium binaries are downloaded implicitly on setup or `emplace.py` is run, by default, we now use the version included with the current pypdfium2 release. This is to prevent possible API breakage when pypdfium2 is installed from source. It should also make the `git` dependency optional on default setup. `update.py` and `craft.py` continue to default to the latest pdfium-binaries version.
- `update.py`: added `--verify` option to confirm authenticity of pdfium-binaries release via SLSA provenance. Requires `slsa-verifier`. Thanks to Benoit Blanchon for the upstream part. Also thanks to ArcticLampyrid for the pointer.
- We finally have a build script that works without Google's toolchain, and instead uses system tools/libraries (`build_native.py`). This has been inspired by the `libpdfium` COPR / `libpdfium-nojs` AUR recipes. Thanks to the respective packagers for showing how to do this. By default, this will use the GCC compiler, but Clang should also work if you set up some symlinks. As of this writing, both passes on our Ubuntu x84_64/arm64 CI.
- On host platforms not covered with `pdfium-binaries`, setup now looks for system/libreoffice pdfium. If this is not available either, `build_native.py` will be triggered. This can also be requested explicitly by setting `PDFIUM_PLATFORM` to `fallback`, `system-search` or `build-native`.
- Reworked setup to expose all targets through `PDFIUM_PLATFORM`. Added proper `system` staging directory. Refactored integration of caller-provided data files to avoid ambiguity. See the updated Readme for details.
- The toolchained build script continues to be available as well, but has been renamed from `sourcebuild.py` to `build_toolchained.py`.
- Both build scripts now pin pdfium to the version last tested by pypdfium2-team.
- By default, the build scripts now generate separate DLLs for dependency libraries, but you may pass `--single-lib` to restore the previous behavior of bundling dependencies into a single pdfium DLL. Setup has been changed accordingly to collect libraries with globbing patterns.
- With `build_toolchained.py --update`, avoid calling `gclient revert` and `gclient sync`, because this seems to sync twice, which is slow. Instead, call only `gclient sync` with `-D --reset`.
- With `pdfium-binaries`, read the full version from the `VERSION` file embedded in the tarballs. This avoids a potentially expensive `git ls-remote` call to get Chromium tags.
- Added `GIVEN_FULLVER` and `IGNORE_FULLVER` env vars to manually set or skip the full version for other targets, also to avoid said web call.
- Use build-specific license files collected by pdfium-binaries. Replaced outdated `LicenseRef-PdfiumThirdParty` with `BUILD_LICENSES/` directory.
- Take `PDFIUM_BINDINGS=reference` into account on sourcebuild as well. Automatically fall back to reference bindings if ctypesgen is not installed (except on CI).
- If packaging with `PDFIUM_PLATFORM=sourcebuild`, forward the platform tag determined by `bdist_wheel`'s wrapper, rather than using the underlying `sysconfig.get_platform()` directly. This may provide more accurate results, e.g. on macOS.
- Avoid needlessly calling `_get_libc_ver()`. Instead, call it only on Linux. A negative side effect of calling this unconditionally is that, on non-Linux platforms, an empty string may be returned, in which case the musllinux handler would be reached, which uses non-public API and isn't meant to be called on other platforms (though it seems to have passed).

*Project*
- Replaced the bash `./run` file with a [`justfile`](https://github.com/casey/just). Note that the runfile previously did not fail fast and propagate errors, which is potentially dangerous for a release workflow. This had been fixed on the runfile in v5.0.0b1 before introducing the justfile.
- CI: Added Linux aarch64 (GH now provides free runners) and Python 3.13 to the test matrix.
- Merged `tests_old/` back into `tests/`.
- Migrated from deprecated `.reuse/dep5` to more visible `REUSE.toml`. Removed non-standard `.reuse/dep5-wheel`.
- Docs: Improved logic when to include the unreleased version warning and upcoming changelog.
- Bumped minimum pdfium requirement in conda recipe to `>6635` (effectively `>=6638`), due to new errchecks.
- Cleanly split out conda packaging into an own file, and confined it to the `conda/` directory, to avoid polluting the main setup code.
