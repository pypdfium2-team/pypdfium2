<!-- SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

## PyPDFium2

[PyPDFium2](https://github.com/pypdfium2-team/pypdfium2) is a Python 3 binding to
[PDFium](https://pdfium.googlesource.com/pdfium/+/refs/heads/main), the liberal-licensed
PDF rendering library authored by Foxit and maintained by Google.


## Install/Update

### Install from PyPI

```bash
python3 -m pip install -U pypdfium2
```

### Source build

```bash
python3 setup_source.py bdist_wheel
pip3 install dist/pypdfium2-${version}-py3-none-${platform_tag}.whl
```


## Examples

### Using the command-line interface

```bash
pypdfium2 -i your_file.pdf -o your_output_dir/ --scale 1 --rotation 0 --optimise-mode none
```

If you want to render multiple files at once, a bash `for`-loop may be suitable:
```bash
for file in ./*.pdf; do echo "$file" && pypdfium2 -i "$file" -o your_output_dir/ --scale 2; done
```

To obtain a list of possible command-line parameters, run
```bash
pypdfium2 --help
```

CLI documentation: https://pypdfium2.readthedocs.io/en/latest/cli.html


### Using the support model

```python3
import pypdfium2 as pdfium

with pdfium.PdfContext(filename) as pdf:
    pil_image = pdfium.render_page(
        pdf,
        page_index = 0,
        scale = 1,
        rotation = 0,
        background_colour = 0xFFFFFFFF,
        render_annotations = True,
        optimise_mode = pdfium.OptimiseMode.none,
    )

pil_image.save("out.png")
```

Support model documentation: https://pypdfium2.readthedocs.io/en/latest/api.html


### Using the PDFium API

```python3
import ctypes
from PIL import Image
import pypdfium2 as pdfium

doc = pdfium.FPDF_LoadDocument(filename, None) # load document (filename, password string)
page_count = pdfium.FPDF_GetPageCount(doc)     # get page count
assert page_count >= 1

page   = pdfium.FPDF_LoadPage(doc, 0)                # load the first page
width  = int(pdfium.FPDF_GetPageWidthF(page)  + 0.5) # get page width
height = int(pdfium.FPDF_GetPageHeightF(page) + 0.5) # get page height

# render to bitmap
bitmap = pdfium.FPDFBitmap_Create(width, height, 0)
pdfium.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, 0xFFFFFFFF)
pdfium.FPDF_RenderPageBitmap(
    bitmap, page, 0, 0, width, height, 0, 
    pdfium.FPDF_LCD_TEXT | pdfium.FPDF_ANNOT
)

# retrieve data from bitmap
cbuffer = pdfium.FPDFBitmap_GetBuffer(bitmap)
buffer = ctypes.cast(cbuffer, ctypes.POINTER(ctypes.c_ubyte * (width * height * 4)))

img = Image.frombuffer("RGBA", (width, height), buffer.contents, "raw", "BGRA", 0, 1)
img.save("out.png")

if bitmap is not None:
    pdfium.FPDFBitmap_Destroy(bitmap)
pdfium.FPDF_ClosePage(page)

pdfium.FPDF_CloseDocument(doc)
```

Documentation for the [PDFium API](https://developers.foxit.com/resources/pdf-sdk/c_api_reference_pdfium/group___f_p_d_f_i_u_m.html)
is available. PyPDFium2 transparently maps all PDFium classes, enums and functions to Python.
However, there can sometimes be minor differences between Foxit and open-source PDFium.
In case of doubts, take a look at the inline source code documentation of PDFium.


## Licensing

PyPDFium2 source code itself is Apache-2.0 licensed.
The auto-generated bindings file contains BSD-3-Clause code.

Documentation and examples are CC-BY-4.0.

PDFium is available by the terms and conditions of either Apache 2.0 or BSD-3-Clause, at your choice.

Various other BSD- and MIT-style licenses apply to the dependencies of PDFium.

License texts for PDFium and its dependencies are included in the file
[`LICENSE-PDFium.txt`](LICENSE-PDFium.txt), which is also shipped with binary re-distributions.


## History

PyPDFium2 is the successor of *pypdfium* and *pypdfium-reboot*.

The initial *pypdfium* was packaged manually and did not get regular updates.
There were no platform-specific wheels, but only a single wheel that contained
binaries for 64-bit Linux, Windows and macOS.

*pypdfium-reboot* then added a script to automate binary deployment and bindings generation
to simplify regular updates. However, it was still not platform specific.

PyPDFium2 is a full rewrite of *pypdfium-reboot* to build platform-specific wheels.
It also adds a basic support model and a command-line interface on top of the PDFium C API
to simplify common use cases.
Moreover, PyPDFium2 includes facilities to build PDFium from source, to extend
platform compatibility.


## Development

PDFium builds are retrieved from [bblanchon/pdfium-binaries](https://github.com/bblanchon/pdfium-binaries).
Python bindings are auto-generated with [ctypesgen](https://github.com/ctypesgen/ctypesgen)

Currently supported architectures:

* macOS x86_64 *
* macOS arm64 *
* Linux x86_64
* Linux aarch64 (64-bit ARM) *
* Linux armv7l (32-bit ARM hard-float, e. g. Raspberry Pi 2)
* Windows 64bit
* Windows 32bit *

`*` Not tested yet

If you have access to a theoretically supported but untested system, please report
success or failure on the issues panel.

(In case `bblanchon/pdfium-binaries` would add support for more architectures, PyPDFium2
could be adapted easily.)

For wheel naming conventions, please see
[Python Packaging: Platform compatibility tags](https://packaging.python.org/specifications/platform-compatibility-tags/)
and the various referenced PEPs.

PyPDFium2 contains scripts to automate the release process:

* To build wheels for all platforms, run `./release.sh`. This will download binaries
  and header files, write finished Python wheels to `dist/`, and run `check-wheel-contents`.
* To clean up after a release, run `./clean.sh`. This will remove downloaded files and
  build artifacts.

### Release packaging

```bash
# download binaries / header files and generate bindings
python3 update.py

# build the package that corresponds to your platform
python3 setup_${platform_name}.py bdist_wheel

# optionally, run check-wheel-contents on the package to confirm its validity
check-wheel-contents dist/pypdfium2-${version}-py3-none-${platform_tag}.whl

# install the package locally
python3 -m pip install -U dist/pypdfium2-${version}-py3-none-${platform_tag}.whl

# remove downloaded files and build artifacts
bash clean.sh
```

### Publishing the wheels

* You may want to upload to [TestPyPI](https://test.pypi.org/legacy/) first to ensure
  everything works as expected:
  ```bash
  twine upload --verbose --repository-url https://test.pypi.org/legacy/ dist/*
  ```
* If all went well, upload to the real PyPI:
  ```bash
  twine upload dist/*
  ```


## Issues

Since PyPDFium2 is built using upstream binaries and an automatic bindings creator,
issues that are not related to packaging most likely need to be addressed upstream.
However, the [PyPDFium2 issues panel](https://github.com/pypdfium2-team/pypdfium2/issues)
is always a good place to start if you have any problems, questions or suggestions.

If the cause of an issue could be determined to be in PDFium, the problem needs to be
reported at the [PDFium bug tracker](https://bugs.chromium.org/p/pdfium/issues/list).

Issues related to build configuration should be discussed at
[pdfium-binaries](https://github.com/bblanchon/pdfium-binaries/issues), though.

If your issue is caused by the bindings generator, refer to the
[ctypesgen bug tracker](https://github.com/ctypesgen/ctypesgen/issues).


## Known limitations

### Non-ascii file paths on Windows

On Windows, PDFium currently is not able to open documents with file names containing multi-byte, non-ascii
characters. This bug is [reported since March 2017](https://bugs.chromium.org/p/pdfium/issues/detail?id=682).
However, the PDFium development team so far has not given it much attention. The cause of the issue
is known and the structure for a fix was proposed, but it has not been applied yet.

This issue cannot reasonably be worked around in PyPDFium2, for the following reasons:

* Using `FPDF_LoadMemDocument()` rather than `FPDF_LoadDocument()` is not possible due to issues with
  concurrent access to the same file. Moreover, it would be less efficient as the whole document has
  to be loaded into memory. This makes it impractical for large files.
* `FPDF_LoadCustomDocument()` is not a solution, since mapping the complex file reading callback to Python
  is hardly feasible. Furthermore, there would likely be the same problem with concurrent access.
* Creating a tempfile with a compatible name would be possible, but cannot be done in PyPDFium2 itself:
  For faster rendering, you usually set up a multiprocessing pool or a concurrent future. This means
  each process has to initialise its own `PdfContext`. If an automatic tempfile workaround were implemented
  in `PdfContext`, this would mean that each process creates its own temporary copy of the file, which
  would be highly inefficient. The tempfile should be created only once for all pages, not for each page
  separately. Therefore, this workaround can only be applied downstream.
  It could be done somewhat like this:
  
  ```python3
  import sys
  
  if sys.platform.startswith('win32') and not filename.isascii():
      # create a temporary copy and remap the file name
      # (str.isascii() requires at least Python 3.7)
      ...
  ```
  
  This workaround is currently used for the command-line interface of PyPDFium2
  (see [`__main__.py`](src/pypdfium2/__main__.py)).
