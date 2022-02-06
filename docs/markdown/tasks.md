<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

Tasks
=====

(These are various tasks for the maintainer to keep in mind, in no specific order.)

* Allow for only returning bytes rather than creating an `Image.Image` object when rendering, so that callers may use the data in any way they like, without having to go through an intermediate PIL object (e. g. directly inject the data into a GUI widget buffer).
* Add capabilities to render a certain area of a page (issue #38).
* Use FPDFBitmap_CreateEx() and the FPDFBitmap_XXX macros for rendering with custom pixel format, to avoid the necessity of converting with PIL afterwards.
* Add missing call to FORM_OnBeforeClosePage(). Also think about possibly using FPDFPage_Flatten() instead of FPDF_FFLDraw().
* Create a support model for progressive rendering (`FPDF_RenderPageBitmap_Start()` & `IFSDK_PAUSE`)
* Set the version appropriately when doing a source build (i. e. append current PDFium commit hash to version string).
* Sourcebuild: regroup patches to be operating system specific.
* Decide what to do about the kind of failed `compcheck.py` utility.
* Think about further extending support for older Python versions (see changelog).
* Create a `.readthedocs.yaml` configuration file (issue #32).
* Look into setting up Github Actions CI.
* Ask Linux distributors to package PDFium, as this could greatly simplify the installation of PyPDFium2 for many users. Since most distributions are already compiling PDFium for their Chromium package anyway, it should be feasible to build PDFium as a dynamically linked library and add a development package containing the header files. We could then add a custom setup file that will create bindings using the system-provided PDFium headers.
