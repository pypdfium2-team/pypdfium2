<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Tasks

These are various tasks for the maintainer to keep in mind, in no specific order.
Also see the issues panel and inline `TODO` marks in source code.

### Main Code
* Research if/how we can efficiently render to ctypes arrays concurrently.
* When rendering with multiple processes and bytes were provided as input, is the memory duplicated or shared? If it's duplicated, find a way to share it or write a tempfile instead.
* When rendering, allow callers to provide an own buffer?
* Move init/destroy into a separate file. Provide public init/destroy functions, given that embedders who deal with long-running applications might not want to have PDFium in memory all the time.
* Make members of `_utils.py` public (move into `misc.py`) ?
* Make the bindings file `_pypdfium.py` public ?
* Investigate other PDFium rendering functions. Ideally, we would want to add margins, flip and color schemes.
* Consolidate and extend the support model.

### Setup Infrastructure
* update_pdfium: add option to download a custom pdfium-binaries release (i. e. not the latest).
* update_pdfium: only generate the bindings file once for all platforms.
* packaging_base: use a class for `VerNamespace` so it can be flushed more easily (?)
* craft_packages: add means to skip platforms for which artefacts are missing.
* setup: improve error messages if binaries/bindings are not present in the platform directory - consider downloading missing binaries implicitly on installation.
* setup: improve binary updating procedure by tracking version of currently present binaries - also consider updating outdated binaries implicitly, or at least do something against the possible mismatch with the version file.
* autorelease: on the long term, switch to a proper configuration file (yaml or something) rather than placing empty indicator files in a directory.
* add a `MANIFEST.in` file to avoid being dependent on the presence of `setuptools-scm`.
* sourcebuild/win: fix dynamic values in `resources.rc`.

### Tests
* Add test case for rendering a PDF with interactive forms.
* Find a better replacement for `importchecker`.

### Documentation
* Add/rewrite remaining Readme sections.

### GitHub Workflows
* release: restructure so that it can be run without the publishing part.
* test_release: make it possible to run this workflow on wheels that are not published yet (will probably need upload-artifact and download-artifact actions).
* test_release: add `pypy` interpreter.
* Add a new workflow to test the build script.
* Set up CodeQL (see `Code security and analysis -> Code scanning` in the settings).

### Miscellaneous
* Ask Linux distributors to package PDFium.
* Add means to plug in PDFium headers/binaries from an arbitrary location, probably using custom environment variables.
* Keep in mind that `ctypes.pythonapi` exists. Maybe we could replace our wonky `id()` based keep-the-object-alive approach with proper incref/decref calls?
