<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Tasks

These are various tasks for the maintainer to keep in mind, in no specific order

### Main Code
* Make the bindings file `_pypdfium.py` public
* Make members of `_utils.py` public (move into `misc.py`)
* Address points listed in [`planned_changes.md`](../source/planned_changes.md)
* Investigate other PDFium rendering functions. Ideally, we would want to add margins, flip and colour schemes. Also consider making form rendering optional.
* Implement `no_antialias` differently (probably it'd be best to provide separate options for each)
* Read up what `FPDFPage_Flatten()` does and if we could use it somehow
* Consolidate and extend the support model

### Setup Infrastructure
* packaging_base: use a class for `VerNamespace` so it can be flushed more easily
* autorelease: address inline TODOs
* update_pdfium: accept `auto` for `--platform` argument
* update_pdfium: add option to download a custom pdfium-binaries release (i. e. not the latest)
* update_pdfium: only generate the bindings file once for all platforms
* update_pdfium: don't skip missing artefacts by default, abort instead
* craft_packages: add means to skip platforms for which artefacts are missing
* setup: improve error messages if binaries/bindings are not present in the platform directory - consider downloading missing binaries implicitly on installation
* setup: improve binary updating procedure by tracking version of currently present binaries - also consider updating outdated binaries implicitly, or at least do something against the possible mismatch with the version file
* add a `MANIFEST.in` file to avoid being dependant on the presence of `setuptools-scm`
* further switch to global variables where it makes sense
* sourcebuild/win: fix dynamic values in `resources.rc`

### Tests
* Add test case for rendering a PDF with interactive forms
* Find a better replacement for `importchecker`

### Documentation
* Move development section of the Readme into a dedicated file and add some more information
* Add a ctypes primer explaining how to interoperate with the PDFium C API

### GitHub Workflows
* release: restructure so that it can be run without the publishing part
* test_release: make it possible to run this workflow on wheels that are not published yet (will probably need upload-artifact and download-artifact actions)
* test_release: add `pypy` interpreter
* Add a new workflow to test the build script
* Set up CodeQL (see `Code security and analysis -> Code scanning` in the settings)

### Miscellaneous
* Ask Linux distributors to package PDFium
* Add means to plug in PDFium headers/binaries from an arbitrary location, probably using custom environment variables
