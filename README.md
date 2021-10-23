<!-- SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

## PyPDFium2

PyPDFium2 is a Python 3 binding to PDFium, the liberal-licensed PDF rendering
library developed by Google.

## Install/Update

### Install from PyPI

```bash
python3 -m pip install -U pypdfium2
```

### Manual installation

```bash
# download binaries / header files and generate bindings
python3 update.py

# build the package that corresponds to your platform
python3 setup_${platform_name}.py bdist_wheel

# install it
python3 -m pip install -U dist/pypdfium2-${version}-py3-none-${platform_tag}.whl

# remove downloaded files and build artifacts
bash clean.sh
```


## Documentation

[API documentation](https://developers.foxit.com/resources/pdf-sdk/c_api_reference_pdfium/group___f_p_d_f_i_u_m.html)
for PDFium is available.
PyPDFium2 transparently maps all PDFium classes, enums and functions to Python.


## Quick Start

```python3
import sys
import ctypes
from PIL import Image
import pypdfium2 as pdfium

pdfium.FPDF_InitLibraryWithConfig(None)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage: example.py somefile.pdf")
        sys.exit()
    
    filename = sys.argv[1]
    
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
    buffer = pdfium.FPDFBitmap_GetBuffer(bitmap)
    buffer_ = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte * (width * height * 4)))

    img = Image.frombuffer("RGBA", (width, height), buffer_.contents, "raw", "BGRA", 0, 1)
    img.save("out.png")
    
    if bitmap is not None:
        pdfium.FPDFBitmap_Destroy(bitmap)
    pdfium.FPDF_ClosePage(page)
    
    pdfium.FPDF_CloseDocument(doc)
```


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
success or failure in the PyPDFium2 bug tracker.

(In case `bblanchon/pdfium-binaries` would add support for more architectures, PyPDFium2
could be adapted easily.)

For wheel naming conventions, please see [Python Packaging / Platform compatibility tags](https://packaging.python.org/specifications/platform-compatibility-tags/) and the various referenced PEPs.

PyPDFium2 contains scripts to automate the release process:

* To build wheels for all platforms, run `./release.sh`. This will download binaries
  and header files, write finished Python wheels to `dist/`, and run `check-wheel-contents`.
* To clean up after a release, run `./clean.sh`. This will remove downloaded files and
  build artifacts.

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


## Licensing

PyPDFium2 deployment scripts are Apache-2.0 licensed.
The auto-generated bindings file contains BSD-3-Clause code.

Documentation and examples are CC-BY-4.0.

PDFium is available by the terms and conditions of either Apache 2.0 or BSD-3-Clause, at your choice.

Various other BSD- and MIT-style licenses apply to the dependencies of PDFium.

License texts for PDFium and its dependencies are included in the file [`LICENSE-PDFium.txt`](LICENSE-PDFium.txt),
which is also shipped with binary re-distributions.


## History

PyPDFium2 is the successor of *pypdfium* and *pypdfium-reboot*.

The initial *pypdfium* was packaged manually and did not get regular updates.
There were no platform-specific wheels, but only one wheel for 64-bit Windows, macOS and
Linux that was misleadingly marked as 'universal'. Overall it was rather a proof of concept.

*pypdfium-reboot* then added a script to automate binary deployment and bindings generation
to simplify regular updates. However, it was still not platform specific.

PyPDFium2 is a full rewrite of *pypdfium-reboot* to build platform-specific wheels.
