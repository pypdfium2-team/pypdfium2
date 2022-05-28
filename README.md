<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# pypdfium2

[pypdfium2](https://github.com/pypdfium2-team/pypdfium2) is a Python 3 binding to [PDFium](https://pdfium.googlesource.com/pdfium/+/refs/heads/main), the liberal-licensed PDF rendering library authored by Foxit and maintained by Google.


## Install/Update

### Install from PyPI

```bash
pip3 install --no-build-isolation -U pypdfium2
```

### Manual installation

The following steps require the system tools `git` and `gcc` to be installed and available in `PATH`.
For Python setup and runtime dependencies, please refer to [`setup.cfg`](./setup.cfg).
It is recommended to install `ctypesgen` from the latest sources (`git master`).

#### Package locally

To get pre-compiled binaries, generate bindings and install pypdfium2, you may run
```bash
make install
```
in the directory you downloaded the repository to. This will resort to building PDFium if no pre-compiled binaries are available for your platform.

#### Source build

If you wish to perform a source build regardless of whether PDFium binaries are available or not, you can try the following:
```bash
make build
```

Depending on the operating system, additional dependencies may need to be installed beforehand.


## Examples

### Using the command-line interface

Rasterise a PDF document:
```bash
pypdfium2 render document.pdf -o output_dir/ --scale 3
```

You may also rasterise multiple files at once:
```bash
pypdfium2 render doc_1.pdf doc_2.pdf doc_3.pdf -o output_dir/
```

Show the table of contents for a PDF:
```bash
pypdfium2 toc document.pdf
```

To obtain a list of subcommands, run `pypdfium2 help`. Individual help for each subcommand is available can be accessed in the same way (`pypdfium any_subcommand help`)

CLI documentation: https://pypdfium2.readthedocs.io/en/stable/shell_api.html


### Using the support model

Import pypdfium2:

```python
import pypdfium2 as pdfium
```

Open a PDF using the helper class `PdfDocument` (supports file paths, bytes, and byte buffers):

```python
pdf = pdfium.PdfDocument(filepath)
print(pdf)
# Work with the helper class
print(pdf.raw)
# Work with the raw PDFium object handle
pdf.close()
```

Render a single page:

```python
pdf = pdfium.PdfDocument(filepath)
page = pdf.get_page(0)

pil_image = page.render_topil(
    scale = 1,
    rotation = 0,
    crop = (0, 0, 0, 0),
    colour = (255, 255, 255, 255),
    annotations = True,
    greyscale = False,
    optimise_mode = pdfium.OptimiseMode.NONE,
)
pil_image.save("out.png")

[g.close() for g in (pil_image, page, pdf)]
```

Render multiple pages concurrently:

```python
pdf = pdfium.PdfDocument(filepath)

n_pages = len(pdf)
page_indices = [i for i in range(n_pages)]
renderer = pdf.render_topil(
    page_indices = page_indices,
)

for image, index in zip(renderer, page_indices):
    image.save('out_%s.jpg' % str(index).zfill(n_pages))
    image.close()

pdf.close()
```

Read the table of contents:

```python
pdf = pdfium.PdfDocument(filepath)

for item in pdf.get_toc():
    print(
        '    ' * item.level +
        '[{}] '.format('-' if item.is_closed else '+') +
        '{} -> {}  # {} {}'.format(
            item.title,
            item.page_index + 1,
            item.view_mode,
            item.view_pos,
        )
    )

pdf.close()
```

Support model documentation: https://pypdfium2.readthedocs.io/en/stable/python_api.html


### Using the PDFium API

Rendering the first page of a PDF document:

```python
import math
import ctypes
import os.path
from PIL import Image
import pypdfium2 as pdfium

filepath = os.path.abspath("tests/resources/render.pdf")

doc = pdfium.FPDF_LoadDocument(filepath, None)
page_count = pdfium.FPDF_GetPageCount(doc)
assert page_count >= 1

form_config = pdfium.FPDF_FORMFILLINFO(2)
form_fill = pdfium.FPDFDOC_InitFormFillEnvironment(doc, form_config)

page = pdfium.FPDF_LoadPage(doc, 0)
width = math.ceil(pdfium.FPDF_GetPageWidthF(page))
height = math.ceil(pdfium.FPDF_GetPageHeightF(page))

bitmap = pdfium.FPDFBitmap_Create(width, height, 0)
pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, 0xFFFFFFFF)

render_args = [bitmap, page, 0, 0, width, height, 0,  pdfium.FPDF_LCD_TEXT | pdfium.FPDF_ANNOT]
pdfium.FPDF_RenderPageBitmap(*render_args)
pdfium.FPDF_FFLDraw(form_fill, *render_args)

cbuffer = pdfium.FPDFBitmap_GetBuffer(bitmap)
buffer = ctypes.cast(cbuffer, ctypes.POINTER(ctypes.c_ubyte * (width * height * 4)))

img = Image.frombuffer("RGBA", (width, height), buffer.contents, "raw", "BGRA", 0, 1)
img.save("out.png")

pdfium.FPDFBitmap_Destroy(bitmap)
pdfium.FPDF_ClosePage(page)

pdfium.FPDFDOC_ExitFormFillEnvironment(form_fill)
pdfium.FPDF_CloseDocument(doc)
```

For more examples of using the raw API, take a look at the [support model source code](src/pypdfium2/_helpers).

Documentation for the [PDFium API](https://developers.foxit.com/resources/pdf-sdk/c_api_reference_pdfium/group___f_p_d_f_i_u_m.html) is available. pypdfium2 transparently maps all PDFium classes, enums and functions to Python. However, there can sometimes be minor differences between Foxit and open-source PDFium. In case of doubt, take a look at the inline source code documentation of PDFium.


## Licensing

PDFium and pypdfium2 are available by the terms and conditions of either Apache 2.0 or BSD-3-Clause, at your choice.

Various other open-source licenses apply to the dependencies of PDFium. License texts for PDFium and its dependencies are included in the file [`LicenseRef-PdfiumThirdParty.txt`](LICENSES/LicenseRef-PdfiumThirdParty.txt), which is also shipped with binary redistributions.

Documentation and examples of pypdfium2 are CC-BY-4.0 licensed.


## In Use

* The [doctr](https://mindee.github.io/doctr/) OCR library uses pypdfium2 to rasterise PDFs.
* [Extract-URLs](https://github.com/elescamilla/Extract-URLs/) use pypdfium2 to extract URLs from PDF documents.
* [py-pdf/benchmarks](https://github.com/py-pdf/benchmarks) compares pypdfium2's text extraction capabilities with other libraries.


## Development

PDFium builds are retrieved from [bblanchon/pdfium-binaries](https://github.com/bblanchon/pdfium-binaries). Python bindings are auto-generated with [ctypesgen](https://github.com/ctypesgen/ctypesgen)

Please see [#3](https://github.com/pypdfium2-team/pypdfium2/issues/3) for a list of platforms where binary wheels are available.
Some wheels are not tested, unfortunately. If you have access to a theoretically supported but untested system, please report success or failure on the issue or discussion panel.

For wheel naming conventions, please see [Python Packaging: Platform compatibility tags](https://packaging.python.org/specifications/platform-compatibility-tags/) and the various referenced PEPs. [This thread](https://discuss.python.org/t/wheel-platform-tag-for-windows/9025/5) may also provide helpful information.

pypdfium2 contains scripts to automate the release process:

* To build the wheels, run `make packaging`. This will download binaries and header files, write finished Python binary distributions to `dist/`, and run some checks.
* To clean up after a release, run `make clean`. This will remove downloaded files and build artefacts.

### Testing

Run `make test`.

### Publishing

The release process is automated using a CI workflow that pushes to GitHub, TestPyPI and PyPI.
To do a release, first run `make packaging` locally to check that everything works as expected.
If all went well, upload changes to the version file and push a new tag to trigger the `Release` woirkflow.
Always make sure the information in `src/pypdfium2/version.py` matches with the tag!
```bash
git tag -a A.B.C
git push --tags
```
Once a new version is released, update the `stable` branch to point at the commit of the latest tag.

## Issues

Since pypdfium2 is built using upstream binaries and an automatic bindings creator, issues that are not related to packaging or support model code probably need to be addressed upstream. However, the [pypdfium2 issues panel](https://github.com/pypdfium2-team/pypdfium2/issues) is always a good place to start if you have any problems, questions or suggestions.

If the cause of an issue could be determined to be in PDFium, the problem needs to be reported at the [PDFium bug tracker](https://bugs.chromium.org/p/pdfium/issues/list).
For discussion and general questions, also consider joining the [PDFium mailing list](https://groups.google.com/g/pdfium/).

Issues related to pre-compiled packages should be discussed at [pdfium-binaries](https://github.com/bblanchon/pdfium-binaries/issues), though.

If your issue is caused by the bindings generator, refer to the [ctypesgen bug tracker](https://github.com/ctypesgen/ctypesgen/issues).


## Known limitations

### Incompatibility with CPython 3.7.6 and 3.8.1

pypdfium2 cannot be used with releases 3.7.6 and 3.8.1 of the CPython interpreter due to a [regression](https://github.com/python/cpython/pull/16799#issuecomment-612353119) that broke ctypesgen-created string handling code.


## Thanks to

* [Anurag Bansal](https://github.com/banagg): Support model for text insertion (`PdfPage.insert_text()`).
* [Benoît Blanchon](https://github.com/bblanchon): Author of [PDFium binaries](https://github.com/bblanchon/pdfium-binaries/) and [patches](sourcebuild/patches/).
* [Anderson Bravalheri](https://github.com/abravalheri): Help with achieving PEP 517/518 compliance.
* [Tim Head](https://github.com/betatim): Original idea for PDFium Python bindings with ctypesgen in `wowpng`.
* [Yinlin Hu](https://github.com/YinlinHu): `pypdfium` prototype and `kuafu` PDF viewer.
* [Adam Huganir](https://github.com/adam-huganir): Initial help and suggestions.
* [kobaltcore](https://github.com/kobaltcore): Bug fix for `PdfDocument.save()`.
* [Mike Kroutikov](https://github.com/mkroutikov): Examples on how to use PDFium with ctypes in `redstork` and `pdfbrain`.
* [Peter Saalbrink](https://github.com/petersaalbrink): Code style improvements to the multipage renderer.
* [Lei Zhang](https://github.com/leizleiz) and [Thomas Sepez](https://github.com/tsepez): Windows-specific fixes concerning `FPDF_LoadDocument()`.


## Fun facts

If you are on Linux, have a recent version of LibreOffice installed, and insist on saving as much disk space as anyhow possible, you can remove the PDFium binary shipped with pypdfium2 and create a symbolic link to the one provided by LibreOffice. This is not recommended, but the following proof-of-concept steps demonstrate that it is possible.
(If using this strategy, it is likely that certain newer methods such as `FPDF_ImportNPagesToOne()` will not be available yet, since the PDFium build of LibreOffice may be a bit older.)

```bash
# Find out where the pypdfium2 installation is located
python3 -m pip show pypdfium2 |grep Location

# Now go to the path you happen to determine
# If pypdfium2 was installed locally (without root privileges), the path will look somewhat like this
cd ~/.local/lib/python3.8/site-packages/

# Descend into the pypdfium2 directory
cd pypdfium2/

# Delete the current PDFium binary
rm pdfium

# Create a symbolic link to the PDFium binary of LibreOffice
# The path might differ depending on the distribution - this is what applies for Ubuntu 20.04
ln -s /usr/lib/libreoffice/program/libpdfiumlo.so pdfium
```

Sadly, mainstream Linux distributors did not create an own package for PDFium, which causes it to be installed separately with every single program that uses it.


## History

pypdfium2 is the successor of *pypdfium* and *pypdfium-reboot*.

The initial *pypdfium* was packaged manually and did not get regular updates. There were no platform-specific wheels, but only a single wheel that contained binaries for 64-bit Linux, Windows and macOS.

*pypdfium-reboot* then added a script to automate binary deployment and bindings generation to simplify regular updates. However, it was still not platform specific.

pypdfium2 is a full rewrite of *pypdfium-reboot* to build platform-specific wheels. It also adds a basic support model and a command-line interface on top of the PDFium C API to simplify common use cases. Moreover, pypdfium2 includes facilities to build PDFium from source, to extend platform compatibility.
