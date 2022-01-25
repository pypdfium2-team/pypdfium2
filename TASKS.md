PyPDFium2 Tasks
===============

(These are various tasks for the maintainer to keep in mind, in no specific order.)

* Ask Linux distributors to package PDFium, as this could greatly simplify the installation of PyPDFium2 for many users.
  Since most distributions are already compiling PDFium for their Chromium package anyway, it should be feasible to
  build PDFium as a dynamically linked library and add a development package containing the header files. We could
  then add a custom setup file that will create bindings using the system-provided PDFium headers.
* Rework the CLI to use subcommands (e. g. `pypdfium2 render`, `pypdfium2 toc`, `pypdfium2 merge`, ...).
  Also consider positional arguments for file input so the commands are shorter to write. Moreover, allow input of
  multiple files at once.
* Support custom output formats for rendering with the CLI.
* Improve getting and setting the version when updating binaries/bindings.
* Set the version appropriately when doing a source build (i. e. append current PDFium commit hash to version string).
* Read the version differently in setup, as shown in `PIL` and `archive-pdf-tools`, because it seems like the `attr:`
  directive (at least under some conditions) does not extract the version value literally (that is, without trying to
  import the module).
* Change `setup.py` to use a pre-compiled platform-specific binary if available. Otherwise, try to do a source build.
  (Maybe ask the user beforehand.) Consider a fallback to system-provided tools if regular build failed.
* Add means for automatic system dependency installation on Linux. Prompt the user for the admin password using `sudo`,
  `pkexec` or similar.
* Remove the KDevelop project from the repository.
* Move Changelog and Contributing Guidelines into the Sphinx documentation.
* Think about how to prevent further growth of the repository root directory.
* Decide what to do about the kind of failed `compcheck.py` utility.
* Look into setting up Github Actions CI.
* Create a `.readthedocs.yaml` configuration file (issue #32). In general, improve RTD configuration to prevent similar
  trouble like issue #53. It would be nice if we could sync RTD with PyPI rather than GitHub, but there currently doesn't
  seem to be an obvious way. Perhaps we should create a dedicated `docs` branch that RTD is synced with, and update that
  branch with every release.
* Add capabilities to render a certain area of a page (issue #38).
* Allow for only returning bytes rather than creating an `Image.Image` object when rendering, so that callers may use the
  data in any way they like, without having to go through an intermediate PIL object (e. g. directly inject the data into
  a GUI widget buffer).
* Investigate what can be done regarding compatiblity with legacy setuptools versions (issue #52).
* Think about further extending support for older Python versions (see changelog).
