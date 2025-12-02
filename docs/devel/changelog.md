<!-- SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- MyST Syntax -->


# Changelog


## 5.2.0 (2025-12-02)

*There was no 5.2.0 release, it failed during TestPyPI upload due to an oversight. pypdfium2 uses GitHub's immutable releases which come with tag protection, so this cannot be fixed.*


## 5.1.0 (2025-11-23)

- Updated PDFium from `7483` to `7529`.
- Added new helpers `textpage.get_textobj()`, `PdfTextObj` and `PdfFont`.
  These helpers currently just cover font info and object-level text extraction, but may be extended in the future.
  For objects of type `FPDF_PAGEOBJ_TEXT`, `PdfPage.get_objects()` and the `PdfObject` constructor will now return `PdfTextObj` rather than just `PdfObject` instances.
  Thanks to Mykola Skrynnyk for the initial proposal.
  <!-- See #392, #391, #358, #325 -->
- Rolled back `musllinux` tag from `1_2` to `1_1`. This was erroneously incremented shortly before `5.0.0`, but the pdfium-binaries do still run on `musllinux_1_1`, probably because they're statically linked.
- `build_toolchained`: Significant portability enhancements. Should now work on Linux CPUs that are unhandled/incomplete upstream (e.g. `aarch64`). Also, building on Windows arm64 natively may now work. Added ability to cross-compile `ppc64le` from `x86_64`. Removed `--use-syslibs` option (use `build_native` instead).
- `build_native`: Fixed Python 3.6/3.7 compatibility. Added `--no-libclang-rt` option.
- Setup: Fixed inclusion of `BUILD_LICENSES/` sub-directories. Added extra licenses for DLLs pulled in by auditwheel. This concerns sourcebuilds/cibuildwheel only. The wheels on PyPI are unaffected.
- Added android targets to `sbuild.yaml` workflow. This does not impact releases, which still use the pdfium-binaries.
- Added i686 (manylinux and musllinux) to cibuildwheel workflow.
  Use an arm64 host (GHA `ubuntu-24.04-arm`) for armv7l builds, which is much faster than with an `x86_64` host. Added armv7l manylinux target (previously just musllinux).
  This does not impact releases yet, but it may in the future.
- CI: Migrated from `macos-13` to `macos-15-intel`.


## 5.0.0 (2025-10-26)

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
- Updated PDFium from `6462` (v4.30.0) rsp. `7323` (v5.0.0b2) to `7483`.
- Added `PdfPosConv` and `PdfBitmap.get_posconv(page)` helper for bidirectional translation between page and bitmap coordinates.
- Added `PdfObject.get_quad_points()` to get the corner points of an image or text object.
- Exposed `PdfPage.flatten()` (previously semi-private `_flatten()`), after having found out how to correctly use it. Added check and updated docs accordingly.
- With `PdfImage.get_bitmap(render=True)`, added `scale_to_original` option (defaults to True) to temporarily scale the image to its native pixel size. This should improve output quality and make the API substantially more useful. Thanks to Lei Zhang for the suggestion.
- Added context manager support to `PdfDocument`, so it can be used in a `with`-statement, because opening from a file path binds a file descriptor (usually on the C side), which should be released explicitly, given OS limits.
- If document loading failed, `err_code` is now assigned to the `PdfiumError` instance so callers may programmatically handle the error subtype. This addresses {issue}`308`.
- In `PdfPage.render()`, added a new option `maybe_alpha` to use a pixel format with alpha channel if page content has transparency, as rendering to a non-alpha bitmap is inefficient with PDFium in this case. Therefore, it is recommended to set this option to True if dynamic (page-dependent) pixel format selection is acceptable. Alternatively, you might want to use only BGRA via `force_bitmap_format=pypdfium2.raw.FPDFBitmap_BGRA` (at the cost of occupying more memory compared to BGR).
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
- Added draft cibuildwheel workflow and configuration, as a second footing for the project (based on the native sourcebuild, see below). In the future, this may allow to stuff some Linux architecture gaps the *quick & dirty* way with emulation, or maybe new native runners. Many thanks to `wojiushixiaobai` for providing the initial workflow and helpful pointers.

*Setup*
- When pdfium binaries are downloaded implicitly on setup or `emplace.py` is run, we now pin the pdfium version by default. This is to prevent possible API breakage when pypdfium2 is installed from source. It should also make the `git` dependency optional on default setup. `update.py` and `craft.py` continue to default to the latest pdfium-binaries version.
- `pdfium-binaries` now use GitHub's new "immutable releases" feature and offer GitHub build provenance attestations, for enhanced supply chain safety. Many thanks to Benoit Blanchon and GitHub team. Conversely, `update.py` now exposes a `--verify` option to mandate checking the attestation, which is enabled in our release workflow. Otherwise, verification will be automatically enabled if the `gh` dependency is installed.
- We finally have a build script that works without Google's toolchain, and instead uses system tools/libraries (`build_native.py`). This has been inspired by the `libpdfium` COPR / `libpdfium-nojs` AUR recipes. Thanks to the respective packagers for showing how to do this. By default, this will use the GCC compiler, but Clang should also work if you set up some symlinks. As of this writing, both passes on our Ubuntu x84_64/arm64 CI.
- On host platforms not covered with `pdfium-binaries`, setup now looks for system/libreoffice pdfium. If this is not available either, `build_native.py` will be triggered. This can also be requested explicitly by setting `PDFIUM_PLATFORM` to `fallback`, `system-search` or `build-native`.
- Reworked setup to expose all targets through `PDFIUM_PLATFORM`. Added proper `system` staging directory. Refactored integration of caller-provided data files to avoid ambiguity. See the updated Readme for details.
- The toolchained build script continues to be available as well, but has been renamed from `sourcebuild.py` to `build_toolchained.py`.
- Both build scripts now pin pdfium to the version last tested by pypdfium2-team.
- With `build_toolchained.py --update`, avoid calling `gclient revert` and `gclient sync`, because this seems to sync twice, which is slow. Instead, call only `gclient sync` with `-D --reset`.
- With `pdfium-binaries`, read the full version from the `VERSION` file embedded in the tarballs. This avoids a potentially expensive `git ls-remote` call to get Chromium tags.
- Also added `GIVEN_FULLVER` and `IGNORE_FULLVER` env vars to manually set or skip the full version for other targets.
- Use build-specific license files collected by pdfium-binaries. Replaced outdated `LicenseRef-PdfiumThirdParty` with `BUILD_LICENSES/` directory.
- Take `PDFIUM_BINDINGS=reference` into account on sourcebuild as well. Automatically fall back to reference bindings if ctypesgen is not installed (except on CI).
- If packaging with `PDFIUM_PLATFORM=sourcebuild`, forward the platform tag determined by `bdist_wheel`'s wrapper, rather than using the underlying `sysconfig.get_platform()` directly. This may provide more accurate results, e.g. on macOS.
- Avoid needlessly calling `_get_libc_ver()`. Instead, call it only on Linux. A negative side effect of calling this unconditionally is that, on non-Linux platforms, an empty string may be returned, in which case the musllinux handler would be reached, which uses non-public API and isn't meant to be called on other platforms (though it seems to have passed).
- Collect libraries with globbing patterns in later setup pipeline. This is a prerequisite in case we want to split off separate DLLs for some dependency libraries in the future (e.g. libjpeg).

*Project*
- Replaced the bash `./run` file with a [`justfile`](https://github.com/casey/just). Note that the runfile previously did not fail fast and propagate errors, which is potentially dangerous for a release workflow. This had been fixed on the runfile in v5.0.0b1 before introducing the justfile.
- CI: Extended test matrices by Linux and Windows ARM64 (GH now provides free runners) and new Python versions.
- Merged `tests_old/` back into `tests/`.
- Migrated from deprecated `.reuse/dep5` to more visible `REUSE.toml`. Removed non-standard `.reuse/dep5-wheel`.
- Docs: Improved logic when to include the unreleased version warning and upcoming changelog.
- Bumped minimum pdfium requirement in conda recipe to `>6635` (effectively `>=6638`), due to new errchecks.
- Cleanly split out conda packaging into an own file, and confined it to the `conda/` directory, to avoid polluting the main setup code.


## 5.0.0b2 (2025-07-31)

- Updated PDFium from `6996` to `7323`.
- See the beta release notes on GitHub [here](https://github.com/pypdfium2-team/pypdfium2/releases/tag/5.0.0b2)


## 5.0.0b1 (2025-02-03)

- Updated PDFium from `6899` to `6996`.
- See the beta release notes on GitHub [here](https://github.com/pypdfium2-team/pypdfium2/releases/tag/5.0.0b1)


## 4.30.1 (2024-12-19)

**NOTE:** This release has been yanked on PyPI due to a text extraction regression introduced in pdfium `6756`. These problems are fixed as of pdfium-binaries `7019`.<br>
If you need any pypdfium2 improvements from this release, you can do e.g.
`PDFIUM_PLATFORM="auto:6462" pip install -v pypdfium2==4.30.1 --no-binary pypdfium2`
to install from the sdist with the previous pdfium version. Ideally, you'll want to migrate to v5.

- Updated PDFium from `6462` to `6899`.
- `PdfPage.get_objects()`: Don't register pageobjects as children, because they don't need to be closed by the caller when part of a page. This avoids excessive caching of weakrefs that are not cleaned up with the object they refer to.
- Fixed another dotted filepath blunder in the `extract-images` CLI. (The `PdfImage.extract()` API is not affected this time.)
- Adapted setup code to `bdist_wheel` relocation (moved from wheel to setuptools).
- Fixed installation with reference bindings (`PDFIUM_BINDINGS=reference`) by actually including them in the sdist and adding a missing `mkdir` call. (In older versions, this can be worked around by cloning the repository and creating the missing directory manually before installation.)
- Fixed sourcebuild on windows by syncing patches with pdfium-binaries.
- Updated test expectations: due to changes in pdfium, some numbers are now slightly different.
- Fixed conda packaging: It is now required to explicitly specify `-c defaults` with `--override-channels`, presumably due to an upstream change.
- Autorelease: Swapped default condition for minor/patch update, as pypdfium2 changes are likely more API-significant than pdfium updates. Added ability for manual override.
- Bumped workflows to Python 3.12.
- Updated docs on licensing.
- *This is expected to be the last release of the v4 series.*


## 4.30.0 (2024-05-09)

*Backported bug fixes / corrections from current development branch.*

- Updated PDFium from `6406` to `6462`.
- Fixed blunder in `PdfImage.extract()` producing an incorrect output path for prefixes containing a dot. In the `extract-images` CLI, this caused all output images of a type to be written to the same path for a document containing a non-extension dot in the filename.
- XFA / rendering CLI: Fixed incorrect recognition of document length. `pdf.init_forms()` must be called before `len(pdf)`.
- Made `get_text_range()` allocation adapt to pdfium version, as `FPDFText_GetText()` has been reverted to UCS-2. (See v4.28 changelog for background.)
- Updated workflows to include both `macos-13` and `macos-14` in test matrices because v13 is Intel and v14 ARM64 on GH actions. Removed python 3.7 testing because not supported anymore on `macos-14` runners.


## 4.29.0 (2024-04-10)

- Updated PDFium from `6337` to `6406`.


## 4.28.0 (2024-03-10)

- Updated PDFium from `6281` to `6337`.
- `get_text_range()`: Fixed a buffer size regression introduced in v4.26.0, caused by an unexpected behavior change in pdfium (thanks @elonzh for the bug report, {issue}`298`). Since that change, it is not possible anymore to tell the exact amount of memory needed, so we have to allocate for the worst case. Therefore, while this problem persists, it is recommended to instead use `get_text_bounded()` where possible.


## 4.27.0 (2024-02-10)

- Updated PDFium from `6233` to `6281`.
- Added ability to define `$CTYPESGEN_PIN` when building sdist via `./run craft pypi --sdist`, which allows to reproduce our sdists when set to the head commit hash of `pypdfium2-team/ctypesgen` at the time of the build to reproduce. Alternatively, you may patch the relevant `pyproject.toml` entry yourself and use `PDFIUM_PLATFORM=sdist python -m build --sdist` as usual.
- Set up Dependabot for GH Actions. Updated dependencies accordingly.


## 4.26.0 (2024-01-10)

- Updated PDFium from `6164` to `6233`.
- Pin ctypesgen in sdist to prevent re-occurrence of {issue}`264` / {issue}`286`. As a drawback, the pin is never committed, so the sdist is not simply reproducible at this time due to dependence on the latest commit hash of the ctypesgen fork at build time.
- Wheel tags: Added back `manylinux2014` in addition to `manylinux_{glibc_ver}` to be on the safe side. Suspected relation to the above issues.


## 4.25.0 (2023-12-10)

- Updated PDFium from `6110` to `6164`.
- Removed multiprocessing from deprecated `PdfDocument.render()` API and replaced with linear rendering. See below for more info.
- setup: Fixed blunder in headers cache logic that would cause existing headers to be always reused regardless of version. *Note, this did not affect release workflows, only local source re-installs.*
- Show path of linked binary in `pypdfium2 -v`.
- conda: Improved installation docs and channel config.
- conda/workflows: Added ability to (re-)build pypdfium2_raw bindings with any given version of pdfium. Fixes {issue}`279`.
- Made reference bindings more universal by including V8, XFA and Skia symbols. This is possible due to the dynamic symbol guards.
- Instruct ctypesgen to exclude some unused alias symbols pulled in from struct tags.
- Improved issue templates, added pull request template.
- Improved ctypesgen (pypdfium2-team fork).

#### Rationale for `PdfDocument.render()` deprecation

- The parallel rendering API unfortunately was an inherent design mistake: Multiprocessing is not meant to transfer large amounts of pixel data from workers to the main process.
- Bitmap transfer is so expensive that it essentially outweighed parallelization, so there was no real performance advantage, only higher memory load.
- As a related problem, the worker pool produces bitmaps at an independent speed, regardless of where the receiving iteration might be, so bitmaps could queue up in memory, possibly causing an enormeous rise in memory consumption over time. This effect was pronounced e.g. with PNG saving via PIL, as seen in Facebook's `nougat` project.
- Instead, each bitmap should be processed (e.g. saved) in the job which created it. Only a minimal, final result should be sent back to the main process (e.g. a file path).
- This means we cannot reasonably provide a generic parallel renderer; instead it needs to be implemented by callers.
- Historically, note that there had been even more faults in the implementation:
  * Prior to `4.22.0`, the pool was always initialized with `os.cpu_count()` processes by default, even when rendering less pages.
  * Prior to `4.20.0`, a full-scale input transfer was conducted on each job (rendering it unusable with bytes input). However, this can and should be done only once on process creation.
- pypdfium2's rendering CLI cleanly re-implements parallel rendering to files. We may want to turn this into an API in the future.

**Due to the potential for serious issues as outlined above, we strongly recommend that end users update and dependants bump their minimum requirement to this version. Callers should move away from `PdfDocument.render()` and use `PdfPage.render()` instead.**


## 4.24.0 (2023-11-10)

- Updated PDFium from `6097` to `6110`.
- Added GitHub issue templates.


## 4.23.1 (2023-10-31)

- No PDFium update.
- Fixed (Test)PyPI upload.


## 4.23.0 (2023-10-31)

*Note: (Test)PyPI upload failed for this release due to an oversight.*

- Updated PDFium from `6070` to `6097`.
- Fixed faulty version repr (avoid trailing `+` if desc is empty).
- Merged conda packaging code, including CI and Readme integration.
- Updated setup code, mainly to support conda.
  * Independent bindings cache. Download headers from pdfium. Extract archive members explicitly.
  * Cleaned up version integration of sourcebuild.
  * Changed `system` platform to generate files according to given version, instead of expecting given files.
  * Added `prepared!` prefix to platform spec, allowing to install with given files.
  * Added `PDFIUM_BINDINGS=reference` to use pre-built bindings when installing from source.
- Updated Readme.


## 4.22.0 (2023-10-19)

- Updated PDFium from `6056` to `6070`.
- Changed `PDFIUM_PLATFORM=none` to strictly exclude all data files. Added new target `system` consuming bindings and version files supplied by the caller.
- Enhanced integration of separate modules. This blazes the trail for conda packaging. We had to move metadata back to `setup.cfg` since we need a dynamic project name, which `pyproject.toml` does not support.
- Major improvements to version integration.
  * Ship version info as JSON files, separately for each submodule. Expose as immutable classes. Legacy members have been retained for backwards compatibility.
  * Autorelease uses dedicated JSON files for state tracking and control.
  * Read version info from `git describe`, providing definite identification.
  * If a local git repo is not available or `git describe` failed (e.g. sdist or shallow checkout), fall back to a supplied version file or the autorelease record. However, you are strongly encouraged to provide a setup that works with `git describe` where possible.
- Added musllinux aarch64 wheel. Thanks to `@jerbob92`.


## 4.21.0 (2023-10-11)

- Updated PDFium from `6002` to `6056`.
- `PdfTextPage.get_text_range()`: Correct the allocation in case of excluded/inserted chars, modify scope to prevent pdfium from reading beyond `range(index, index+count)` (which otherwise it does with leading excluded chars). Update docs to note the two different representations. Thanks to Nikita Rybak for the discovery ({issue}`261`).

- Setup changes (partly ported from the devel branch)
  * ctypesgen fork: replaced the old, bloated library loader with a new, lean version
  * Merged `$PDFIUM_VERSION` and `$PDFIUM_USE_V8` into the existing `$PDFIUM_PLATFORM` specifier (see Readme for updated description).
  * Removed the `build` package from pyproject buildsystem requires, where it was unnecessary. Thanks to Anaconda Team.
  * Split in two separate modules: pypdfium2 for helpers (pure-python), pypdfium2_raw for the core bindings (data files).

- Switched PyPI upload to "trusted publishing" (OIDC), which is considered safer. Further, the core maintainers have set up 2FA as requested by PyPI.

*Note: Earlier releases may fail to install from source due to API-breaking changes to our ctypesgen fork (see {issue}`264`). Where possible, avoid source installs and use the wheels instead (the default behavior). If you actually have to do this, consider `--no-build-isolation` and pre-installed dependencies, including ctypesgen prior to commit `61c638b`.*

*Warning: musllinux wheels prior to pdfium-binaries `6043` might be invalid.*


## 4.21.0b1 (2023-09-14)

- Updated PDFium from `5989` to `6002`.


## 4.20.0 (2023-09-10)

*This release backports some key fixes/improvements from the development branch*

- Updated PDFium from `5975` to `5989`.
- [V8/XFA] Fixed XFA init. This issue was caused by a typo in a struct field. Thanks to Benoît Blanchon.
- [ctypesgen fork] Prevent setting nonexistent struct fields.
- [V8/XFA] Expose V8/XFA exclusive members in the bindings file by passing ctypesgen the pre-processor defines in question.
- Fixed some major non-API implementation issues with multipage rendering:
  * Avoid full state data transfer and object re-initialization for each job. Instead, use a pool initializer and exploit global variables. This also makes bytes input tolerable for parallel rendering.
  * In the CLI, use a custom converter to save directly in workers instead of serializing bitmaps to the main process.
- Set pdfium version fields to unknown for `PDFIUM_PLATFORM=none` (sdist). This prevents encoding a potentially incorrect version. Also improve CLI version print.
- Fixed sourcebuild with system libraries.
- Fixed RTD build (`system_packages` option removal).
- Attempt to fix automatic GH pages rebuild on release.


## 4.19.0 (2023-08-28)

- Updated PDFium from `5868` to `5975`.
- Reset main branch to stable and shifted v5 development to a branch, so that pdfium updates (and possibly bug fixes) can still be handled. v5 development is delayed and unexpectedly tough, so this seemed necessary.
- The automated schedule has been slowed down from weekly to monthly for the time being. Further manual releases may be triggered as necessary.


## 4.18.0 (2023-07-04)

- Updated PDFium from `5854` to `5868`.


## 4.17.0 (2023-06-27)

- Updated PDFium from `5841` to `5854`.


## 4.16.0 (2023-06-20)

- Updated PDFium from `5827` to `5841`.


## 4.15.0 (2023-06-13)

- Updated PDFium from `5813` to `5827`.
- In helpers, closing a parent object now automatically closes the children to ensure correct order.
  This notably enhances safety of closing and absorbs the common mistake of closing a parent but missing child close calls. See commit [eb07605](https://github.com/pypdfium2-team/pypdfium2/commit/eb07605fcac124b4fe68f6baf60c86183170d259) for more info.
- In `init_forms()`, attempt to call `FPDF_LoadXFA()` and warn on failure, though as of this writing it always fails.


## 4.14.0 (2023-06-06)

- Updated PDFium from `5799` to `5813`.


## 4.13.0 (2023-05-30)

- Updated PDFium from `5786` to `5799`.


## 4.12.0 (2023-05-23)

- Updated PDFium from `5772` to `5786`.


## 4.11.0 (2023-05-16)

- Updated PDFium from `5758` to `5772`.
- In `PdfDocument.render()`, fixed a bad `bitmap.close()` call that would lead to a downstream use after free when using the combination of foreign bitmap and no-copy conversion. Using foreign bitmaps was not the default and expressly not recommended.


## 4.10.0 (2023-05-09)

- Updated PDFium from `5744` to `5758`.


## 4.9.0 (2023-05-02)

- Updated PDFium from `5731` to `5744`.


## 4.8.0 (2023-04-25)

- Updated PDFium from `5715` to `5731`.
- `PdfTextPage.get_rect()`: Added missing return code check and updated docs regarding dependence on `count_rects()`.
  Fixed related test code that was broken but disabled by accident (missing asserts). Thanks to Guy Rosin for reporting {issue}`207`.
- Added `PdfImage.get_size()` wrapping the new pdfium function `FPDFImageObj_GetImagePixelSize()`, which is faster than getting image size through the metadata.
- `build_pdfium.py --use-syslibs`: Changed `sysroot="/"` (invalid) to `use_sysroot=false` (valid). This allows us to remove a botched patch.


## 4.7.0 (2023-04-18)

- Updated PDFium from `5705` to `5715`.
- Fixed `PdfPage.remove_obj()` wrongly retaining the page as parent in the finalizer hierarchy.


## 4.6.0 (2023-04-11)

- Updated PDFium from `5692` to `5705`.


## 4.5.0 (2023-04-04)

- Updated PDFium from `5677` to `5692`.
- In pdfium-binaries, forms init for V8/XFA enabled builds was fixed by correctly setting up XFA on library init
  (see [pdfium-binaries#105](https://github.com/bblanchon/pdfium-binaries/issues/105)).
  Updated pypdfium2's support model accordingly.


## 4.4.0 (2023-03-28)

- Updated PDFium from `5664` to `5677`.


## 4.3.0 (2023-03-21)

- Updated PDFium from `5648` to `5664`.
- Fixed forms rendering in the multi-page renderer by initializing a formenv in worker jobs if the triggering document has one.


## 4.2.0 (2023-03-14)

- Updated PDFium from `5633` to `5648`.
- API-breaking changes around forms code, necessary to fix conceptual issues. Closes {issue}`182`.
  * `may_init_forms` parameter replaced with `init_forms()`, so that a custom form config can be provided.
  * `formtype` attribute replaced with `get_formtype()`.
    Previously, `formtype` would only be set correctly on formenv init, which caused confusion
    for documents that have forms but no formenv was initialized.
- `PdfPage.get_*box()` functions now provide an option to disable fallbacks. Closes {issue}`187`.
- Some formerly hidden utilities are now exposed in the new namespace `pypdfium2.internal`.


## 4.1.0 (2023-03-07)

- Updated PDFium from `5619` to `5633`.
- The `PdfDocument` parameter `may_init_forms` is now False by default.


## 4.0.0 (2023-02-28)

- Updated PDFium from `5579` to `5619`.
- Full support model rewrite. Many existing features changed and new helpers added. Numerous bugs fixed on the way.
  Read the updated documentation to migrate your code.
- The raw API is now isolated in a separate namespace (`pypdfium2.raw`).
  Moreover, the raw API bindings do not implicitly encode strings anymore (pypdfium2 is now built with a patched version of ctypesgen by default).
- Helper objects now automatically resolve to the underlying raw object if used as ctypes function parameter.
- Overhauled the code base to use `pathlib` and f-strings.
- Updated wheel tags.
- Improved command-line interface, setup code, and documentation.


## 4.0.0b2 (2023-02-23)

- First successful beta release for v4.


## 4.0.0b1 (2023-02-22)

- Attempted beta release for v4. PyPI upload failed due to {issue}`177`.


## History

pypdfium2 is on PyPI since Dec 3, 2021. New versions have been released on a regular basis ever since.

There have been the following version ranges: `0.1 - 0.15`, `1.0 - 1.11`, `2.0 - 2.11`, `3.0 - 3.21.1`.

Entries for releases below version 4 have been removed from the changelog because they were too inconsistent.
