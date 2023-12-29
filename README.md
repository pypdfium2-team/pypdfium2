<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# pypdfium2

[![Downloads](https://pepy.tech/badge/pypdfium2/month)](https://pepy.tech/project/pypdfium2)

[pypdfium2](https://github.com/pypdfium2-team/pypdfium2) is an [ABI-level](#drawbacks-of-abi-level-bindings) Python 3 binding to [PDFium](https://pdfium.googlesource.com/pdfium/+/refs/heads/main), a powerful and liberal-licensed library for PDF rendering, inspection, manipulation and creation.

It is built with [ctypesgen](https://github.com/pypdfium2-team/ctypesgen) and external [PDFium binaries](https://github.com/bblanchon/pdfium-binaries/).
The custom setup infrastructure provides a seamless packaging and installation process. A wide range of platforms is supported with pre-built packages.

pypdfium2 includes helpers to simplify common use cases, while the raw PDFium/ctypes API remains accessible as well.


## Installation

<!-- FIXME is there a better/universal way to create linkable sub-sections without them being a heading? Note, the current solution is specific to GH and doesn't work on RTD. -->

* <a id="user-content-install-pypi" class="anchor" href="#install-pypi">From PyPI 🔗</a> (recommended)
  ```bash
  python -m pip install -U pypdfium2
  ```
  This will use a pre-built wheel package, the easiest way of installing pypdfium2.


* <a id="user-content-install-source" class="anchor" href="#install-source">From source 🔗</a>
  
  * Dependencies:
    - System: git, C pre-processor (e.g. gcc, has to be in `$PATH`)
    - Python: ctypesgen (pypdfium2-team fork), wheel, setuptools. Usually installed automatically.
  
  * Get the code
    ```
    git clone "https://github.com/pypdfium2-team/pypdfium2.git"
    cd pypdfium2/
    ```
  
  * <a id="user-content-install-source-default" class="anchor" href="#install-source-default">With pre-built binary 🔗</a>
    ```bash
    # In the pypdfium2/ directory
    python -m pip install -v .
    ```
    A binary is downloaded implicitly from `pdfium-binaries` and bundled into pypdfium2.
  
  * <a id="user-content-install-source-selfbuilt" class="anchor" href="#install-source-selfbuilt">With self-built binary 🔗</a>
    ```bash
    # call build script with --help to list options
    python setupsrc/pypdfium2_setup/build_pdfium.py
    PDFIUM_PLATFORM="sourcebuild" python -m pip install -v .
    ```
    Building PDFium may take a long time, as it comes with its bundled toolchain and deps, rather than taking them from the system.[^pdfium_buildsystem]
    However, we can at least provide the `--use-syslibs` option to build against system-provided runtime libraries.
  
  * <a id="user-content-install-source-system" class="anchor" href="#install-source-system">With system-provided binary 🔗</a>
    ```bash
    # Substitute $PDFIUM_VER with the system pdfium's build version.
    # For ABI safety reasons, you'll want to make sure `$PDFIUM_VER` is correct and the bindings are rebuilt whenever system pdfium is updated.
    PDFIUM_PLATFORM="system:$PDFIUM_VER" python -m pip install -v .
    ```
    Link against external pdfium instead of bundling it.
    Note, this is basically a high-level convenience entry point to internal bindings generation, and intended for end users. Therefore it is less flexible, supporting only the "simple case" for now.
    For more sohpisticated use cases that need passing custom parameters to ctypesgen (e.g. runtime libdirs / headers / feature flags), consider [caller-provided data files](#install-source-caller).
  
  <!-- TODO version.json: reconsider origin - should we add a new field for the packager? -->
  * <a id="user-content-install-source-caller" class="anchor" href="#install-source-caller">With caller-provided data files 🔗</a> (this is expected to work offline)
    ```bash
    # Call ctypesgen (see --help or packaging_base.py::run_ctypesgen() for further options)
    # Reminder: you'll want to use the pypdfium2-team fork of ctypesgen
    ctypesgen --library pdfium --runtime-libdirs $MY_LIBDIRS --headers $MY_INCLUDE_DIR/fpdf*.h -o src/pypdfium2_raw/bindings.py --strip-build-path=. [-D $MY_FLAGS]
    
    # Write the version file (fill the placeholders).
    # Note, this is not a mature interface yet and might change!
    # major/minor/build/patch: integers forming the pdfium version being packaged
    # n_commits/hash: git describe like post-tag info (0/null for release commit)
    # origin: a string to identify the build, consisting of binary source and package provider (e.g. "system/debian", "pdfium-binaries/debian")
    # flags: a comma-delimited list of pdfium feature flag strings (e.g. "V8", "XFA") - may be empty for default build
    cat >"src/pypdfium2_raw/version.json" <<END
    {
      "major": $PDFIUM_MAJOR,
      "minor": $PDFIUM_MINOR,
      "build": $PDFIUM_BUILD,
      "patch": $PDFIUM_PATCH,
      "n_commits": $POST_TAG_COMMIT_COUNT,
      "hash": $POST_TAG_HASH,
      "origin": "$ORIGIN",
      "flags": [$MY_FLAGS]
    }
    END
    
    # optional: copy in a binary if bundling
    cp "$BINARY_PATH" src/pypdfium2_raw/libpdfium.so
    
    # Finally, install
    # set $MY_PLATFORM to "system" if building against system pdfium, "auto" or the platform name otherwise
    PDFIUM_PLATFORM='prepared!$MY_PLATFORM:$PDFIUM_BUILD' python -m pip install --no-build-isolation -v .
    ```
  
  See [Setup Magic](#setup-magic) for details.
  
  Support for source installs (esp. with self-built/system pdfium) is limited, as their integrity depends somewhat on a correctly acting caller.
  
  Installing an `sdist` does not implicitly trigger a sourcebuild if no pre-built binary is available. It is preferred to let callers decide consciously what to do, and run the build script without pip encapsulation.
  
  Relevant pip options:
  * `-v`: Verbose logging output. Useful for debugging.
  * `-e`: Install in editable mode, so the installation points to the source tree. This way, changes directly take effect without needing to re-install. Recommended for development.
  * `--no-build-isolation`: Do not isolate setup in a virtual env; use the main env instead. This renders `pyproject.toml [build-system]` inactive, setup deps must be prepared by caller. Useful to install custom versions of setup deps, or as speedup when installing repeatedly.
  
  [^pdfium_buildsystem]: This means pdfium may not compile on arbitrary hosts. The script is limited to build hosts supported by Google's toolchain. Ideally, we'd need an alternative build system that runs with system packages instead.


* <a id="user-content-install-conda" class="anchor" href="#install-conda">From Conda 🔗</a>
  
  _**Beware:** Any conda packages/recipes of pypdfium2 or pdfium-binaries that might be provided by other distributors, including `anaconda/main` or `conda-forge` default channels, are [unofficial](#install-unofficial)._
  
  + To install
    
    With permanent channel config (encouraged):
    ```bash
    conda config --add channels bblanchon
    conda config --add channels pypdfium2-team
    conda config --set channel_priority strict
    conda install pypdfium2-team::pypdfium2_helpers
    ```
    
    Alternatively, with temporary channel config:
    ```bash
    conda install pypdfium2-team::pypdfium2_helpers --override-channels -c pypdfium2-team -c bblanchon
    ```
    
    Adding the channels permanently and tightening priority is encouraged to include pypdfium2 in `conda update` by default, and to avoid accidentally replacing the install with a different channel. (If desired, you may limit the channel config to the current environment by adding `--env`.)
    Otherwise, you should be cautious when making changes to the environment.
  
  + To depend on pypdfium2 in a `conda-build` recipe
    ```yaml
    requirements:
      run:
        - pypdfium2-team::pypdfium2_helpers
    ```
    You'll want to have downstream callers handle the custom channels as shown above, otherwise conda will not be able to satisfy requirements.
  
  + To set up channels in a GH workflow
    ```yaml
    - name: ...
      uses: conda-incubator/setup-miniconda@v2
      with:
        # ... your options
        channels: pypdfium2-team,bblanchon
        channel-priority: strict
    ```
    This is just a suggestion, you can also call `conda config` manually, or pass channels on command basis using `-c`, as discussed above.
  
  + To verify the sources
    ```bash
    conda list --show-channel-urls "pypdfium2|pdfium-binaries"
    conda config --show-sources
    ```
    The table should show `pypdfium2-team` and `bblanchon` in the channels column.
    If added permanently, the config should also include these channels, ideally with top priority.
    Please check this before reporting any issue with a conda install of pypdfium2.
  
  _**Note:** Conda packages are normally managed using recipe feedstocks driven by third parties, in a Linux repository like fashion. However, with some quirks it is also possible to do conda packaging within the original project and publish to a custom channel, which is what pypdfium2-team does, and the above instructions are referring to._


* <a id="user-content-install-unofficial" class="anchor" href="#install-unofficial">Unofficial packages 🔗</a>
  
  The authors of this project have no control over and are not responsible for possible third-party builds of pypdfium2, and we do not support them. Please use the official packages where possible.
  If you have an issue with a third-party build, either contact your distributor, or try to reproduce with an official build.
  
  Do not expect us to help with the creation of unofficial builds or add/change code for downstream setup tasks. Related issues or PRs may be closed without further notice if we don't see fit for upstream.
  
  If you are a third-party distributor, please point out clearly and visibly in the description that your package is unofficial, i.e. not affiliated with or endorsed by pypdfium2 team.


### Runtime Dependencies

As of this writing, pypdfium2 does not need any mandatory runtime dependencies apart from Python itself.

However, some optional support model features require additional packages:
* [`Pillow`](https://pillow.readthedocs.io/en/stable/) (module name `PIL`) is a pouplar imaging library for Python. pypdfium2 provides convenience methods to translate between raw bitmap buffers and PIL images.
* [`NumPy`](https://numpy.org/doc/stable/index.html) is a library for scientific computing. Similar to `Pillow`, pypdfium2 provides helpers to get a numpy array view of a raw bitmap.


### Setup Magic

As pypdfium2 requires a C extension and has custom setup code, there are some special features to consider. Note, the APIs below may change any time and are mostly of internal interest.

* Binaries are stored in platform-specific sub-directories of `data/`, along with bindings and version information.

* `$PDFIUM_PLATFORM` defines which binary to include on setup.
  - Format spec: `[$PLATFORM][-v8][:$VERSION]` (`[]` = segments, `$CAPS` = variables).
  - Examples: `auto`, `auto:5975` `auto-v8:5975` (`auto` may be substituted by an explicit platform name, e.g. `linux_x64`).
  - Platform:
    + If unset or `auto`, the host platform is detected and a corresponding binary will be selected.
    + If an explicit platform identifier (e.g. `linux_x64`, `darwin_arm64`, ...), binaries for the requested platform will be used.[^platform_ids]
    + If `system`, bind against system-provided pdfium instead of embedding a binary. Version must be given explicitly so matching bindings can be generated.
    + If `sourcebuild`, binaries will be taken from `data/sourcebuild/`, assuming a prior run of `build_pdfium.py`.
    + If `none`, no platform-dependent files will be included, so as to create a source distribution.
    `sourcebuild` and `none` are standalone, they cannot be followed by additional specifiers.
  - V8: If given, use the V8 (JavaScript) and XFA enabled pdfium binaries. Otherwise, use the regular (non-V8) binaries.
  - Version: If given, use the specified pdfium-binaries release. Otherwise, use the latest one.
  - It is possible to prepend `prepared!` to install with existing platform files instead of generating on the fly; the value will be used for metadata / file inclusion. This can be helpful when installing in an isolated env where ctypesgen is not available, but it is not desirable to use the reference bindings (e.g. conda).

* `$PYPDFIUM_MODULES=[raw,helpers]` defines the modules to include. Metadata adapts dynamically.
  - May be used by packagers to decouple raw bindings and helpers, which may be relevant if packaging against system pdfium.
  - Would also allow to install only the raw module without helpers, or only helpers with a custom raw module.

* `$PDFIUM_BINDINGS=reference` allows to override ctypesgen and use the reference bindings file `autorelease/bindings.py` instead.
  - This is a convenience option to get pypdfium2 installed from source even if a working ctypesgen is not available in the install env.
  - Warning: This may not be ABI-safe. Please make sure binary/bindings build headers match to avoid ABI issues.

[^platform_ids]: Intended for packaging, so that wheels can be crafted for any platform without access to a native host.


## Usage

### [Support model](https://pypdfium2.readthedocs.io/en/stable/python_api.html)

<!-- TODO demonstrate more APIs (e. g. XObject placement, transform matrices, image extraction, ...) -->

Here are some examples of using the support model API.

* Import the library
  ```python
  import pypdfium2 as pdfium
  ```

* Open a PDF using the helper class `PdfDocument` (supports file path strings, bytes, and byte buffers)
  ```python
  pdf = pdfium.PdfDocument("./path/to/document.pdf")
  version = pdf.get_version()  # get the PDF standard version
  n_pages = len(pdf)  # get the number of pages in the document
  page = pdf[0]  # load a page
  ```

* Render the page
  ```python
  bitmap = page.render(
      scale = 1,    # 72dpi resolution
      rotation = 0, # no additional rotation
      # ... further rendering options
  )
  pil_image = bitmap.to_pil()
  pil_image.show()
  ```

* Try some page methods
  ```python
  # Get page dimensions in PDF canvas units (1pt->1/72in by default)
  width, height = page.get_size()
  # Set the absolute page rotation to 90° clockwise
  page.set_rotation(90)
  
  # Locate objects on the page
  for obj in page.get_objects():
      print(obj.level, obj.type, obj.get_pos())
  ```

* Extract and search text
  ```python
  # Load a text page helper
  textpage = page.get_textpage()
  
  # Extract text from the whole page
  text_all = textpage.get_text_range()
  # Extract text from a specific rectangular area
  text_part = textpage.get_text_bounded(left=50, bottom=100, right=width-50, top=height-100)
  
  # Locate text on the page
  searcher = textpage.search("something", match_case=False, match_whole_word=False)
  # This returns the next occurrence as (char_index, char_count), or None if not found
  first_occurrence = searcher.get_next()
  ```

<!-- TOC API will change with the next major release -->
* Read the table of contents
  ```python
  for item in pdf.get_toc():
      state = "*" if item.n_kids == 0 else "-" if item.is_closed else "+"
      target = "?" if item.page_index is None else item.page_index+1
      print(
          "    " * item.level +
          "[%s] %s -> %s  # %s %s" % (
              state, item.title, target, item.view_mode, item.view_pos,
          )
      )
  ```

* Create a new PDF with an empty A4 sized page
  ```python
  pdf = pdfium.PdfDocument.new()
  width, height = (595, 842)
  page_a = pdf.new_page(width, height)
  ```

* Include a JPEG image in a PDF
  ```python
  pdf = pdfium.PdfDocument.new()
  
  image = pdfium.PdfImage.new(pdf)
  image.load_jpeg("./tests/resources/mona_lisa.jpg")
  width, height = image.get_size()
  
  matrix = pdfium.PdfMatrix().scale(width, height)
  image.set_matrix(matrix)
  
  page = pdf.new_page(width, height)
  page.insert_obj(image)
  page.gen_content()
  ```

* Save the document
  ```python
  # PDF 1.7 standard
  pdf.save("output.pdf", version=17)
  ```

### Raw PDFium API

While helper classes conveniently wrap the raw PDFium API, it may still be accessed directly and is available in the namespace `pypdfium2.raw`. Lower-level helpers that may aid with using the raw API are provided in `pypdfium2.internal`.

```python
import pypdfium2.raw as pdfium_c
import pypdfium2.internal as pdfium_i
```

Since PDFium is a large library, many components are not covered by helpers yet. You may seamlessly interact with the raw API while still using helpers where available. When used as ctypes function parameter, helper objects automatically resolve to the underlying raw object (but you may still access it explicitly if desired):
```python
permission_flags = pdfium_c.FPDF_GetDocPermission(pdf.raw)  # explicit
permission_flags = pdfium_c.FPDF_GetDocPermission(pdf)      # implicit
```

For PDFium docs, please look at the comments in its [public header files](https://pdfium.googlesource.com/pdfium/+/refs/heads/main/public/).[^pdfium_docs]
A large variety of examples on how to interface with the raw API using [`ctypes`](https://docs.python.org/3/library/ctypes.html) is already provided with [support model source code](src/pypdfium2/_helpers).
Nonetheless, the following guide may be helpful to get started with the raw API, especially for developers who are not familiar with `ctypes` yet.

[^pdfium_docs]: Unfortunately, no recent HTML-rendered docs are available for PDFium at the moment.

<!-- TODO write something about weakref.finalize(); add example on creating a C page array -->

* In general, PDFium functions can be called just like normal Python functions.
  However, parameters may only be passed positionally, i. e. it is not possible to use keyword arguments.
  There are no defaults, so you always need to provide a value for each argument.
  ```python
  # arguments: filepath (bytes), password (bytes|None)
  # null-terminate filepath and encode as UTF-8
  pdf = pdfium_c.FPDF_LoadDocument((filepath+"\x00").encode("utf-8"), None)
  ```
  This is the underlying bindings declaration,[^bindings_decl] which loads the function from the binary and
  contains the information required to convert Python types to their C equivalents.
  ```python
  if _libs["pdfium"].has("FPDF_LoadDocument", "cdecl"):
      FPDF_LoadDocument = _libs["pdfium"].get("FPDF_LoadDocument", "cdecl")
      FPDF_LoadDocument.argtypes = [FPDF_STRING, FPDF_BYTESTRING]
      FPDF_LoadDocument.restype = FPDF_DOCUMENT
  ```
  Python `bytes` are converted to `FPDF_STRING` by ctypes autoconversion.
  When passing a string to a C function, it must always be null-terminated, as the function merely receives a pointer to the first item and then continues to read memory until it finds a null terminator.
  
[^bindings_decl]: From the auto-generated bindings file. We maintain a reference copy at `autorelease/bindings.py`. Or if you have an editable install, there will also be `src/pypdfium2_raw/bindings.py`.

* While some functions are quite easy to use, things soon get more complex.
  First of all, function parameters are not only used for input, but also for output:
  ```python
  # Initialise an integer object (defaults to 0)
  c_version = ctypes.c_int()
  # Let the function assign a value to the c_int object, and capture its return code (True for success, False for failure)
  ok = pdfium_c.FPDF_GetFileVersion(pdf, c_version)
  # If successful, get the Python int by accessing the `value` attribute of the c_int object
  # Otherwise, set the variable to None (in other cases, it may be desired to raise an exception instead)
  version = c_version.value if ok else None
  ```

* If an array is required as output parameter, you can initialise one like this (in general terms):
  ```python
  # long form
  array_type = (c_type * array_length)
  array_object = array_type()
  # short form
  array_object = (c_type * array_length)()
  ```
  Example: Getting view mode and target position from a destination object returned by some other function.
  ```python
  # (Assuming `dest` is an FPDF_DEST)
  n_params = ctypes.c_ulong()
  # Create a C array to store up to four coordinates
  view_pos = (pdfium_c.FS_FLOAT * 4)()
  view_mode = pdfium_c.FPDFDest_GetView(dest, n_params, view_pos)
  # Convert the C array to a Python list and cut it down to the actual number of coordinates
  view_pos = list(view_pos)[:n_params.value]
  ```

* For string output parameters, callers needs to provide a sufficiently long, pre-allocated buffer.
  This may work differently depending on what type the function requires, which encoding is used, whether the number of bytes or characters is returned, and whether space for a null terminator is included or not. Carefully review the documentation for the function in question to fulfill its requirements.
  
  Example A: Getting the title string of a bookmark.
  ```python
  # (Assuming `bookmark` is an FPDF_BOOKMARK)
  # First call to get the required number of bytes (not characters!), including space for a null terminator
  n_bytes = pdfium_c.FPDFBookmark_GetTitle(bookmark, None, 0)
  # Initialise the output buffer
  buffer = ctypes.create_string_buffer(n_bytes)
  # Second call with the actual buffer
  pdfium_c.FPDFBookmark_GetTitle(bookmark, buffer, n_bytes)
  # Decode to string, cutting off the null terminator
  # Encoding: UTF-16LE (2 bytes per character)
  title = buffer.raw[:n_bytes-2].decode("utf-16-le")
  ```
  
  Example B: Extracting text in given boundaries.
  ```python
  # (Assuming `textpage` is an FPDF_TEXTPAGE and the boundary variables are set)
  # Store common arguments for the two calls
  args = (textpage, left, top, right, bottom)
  # First call to get the required number of characters (not bytes!) - a possible null terminator is not included
  n_chars = pdfium_c.FPDFText_GetBoundedText(*args, None, 0)
  # If no characters were found, return an empty string
  if n_chars <= 0:
      return ""
  # Calculate the required number of bytes (UTF-16LE encoding again)
  n_bytes = 2 * n_chars
  # Initialise the output buffer - this function can work without null terminator, so skip it
  buffer = ctypes.create_string_buffer(n_bytes)
  # Re-interpret the type from char to unsigned short as required by the function
  buffer_ptr = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ushort))
  # Second call with the actual buffer
  pdfium_c.FPDFText_GetBoundedText(*args, buffer_ptr, n_chars)
  # Decode to string (You may want to pass `errors="ignore"` to skip possible errors in the PDF's encoding)
  text = buffer.raw.decode("utf-16-le")
  ```

* Not only are there different ways of string output that need to be handled according to the requirements of the function in question.
  String input, too, can work differently depending on encoding and type.
  We have already discussed `FPDF_LoadDocument()`, which takes a UTF-8 encoded string as `char *`.
  A different examples is `FPDFText_FindStart()`, which needs a UTF-16LE encoded string, given as `unsigned short *`:
  ```python
  # (Assuming `text` is a str and `textpage` an FPDF_TEXTPAGE)
  # Add the null terminator and encode as UTF-16LE
  enc_text = (text + "\x00").encode("utf-16-le")
  # cast `enc_text` to a c_ushort pointer
  text_ptr = ctypes.cast(enc_text, ctypes.POINTER(ctypes.c_ushort))
  search = pdfium_c.FPDFText_FindStart(textpage, text_ptr, 0, 0)
  ```

* Leaving strings, let's suppose you have a C memory buffer allocated by PDFium and wish to read its data.
  PDFium will provide you with a pointer to the first item of the byte array.
  To access the data, you'll want to re-interpret the pointer using `ctypes.cast()` to encompass the whole array:
  ```python
  # (Assuming `bitmap` is an FPDF_BITMAP and `size` is the expected number of bytes in the buffer)
  buffer_ptr = pdfium_c.FPDFBitmap_GetBuffer(bitmap)
  buffer_ptr = ctypes.cast(buffer_ptr, ctypes.POINTER(ctypes.c_ubyte * size))
  # Buffer as ctypes array (referencing the original buffer, will be unavailable as soon as the bitmap is destroyed)
  c_array = buffer_ptr.contents
  # Buffer as Python bytes (independent copy)
  data = bytes(c_array)
  ```

* Writing data from Python into a C buffer works in a similar fashion:
  ```python
  # (Assuming `buffer_ptr` is a pointer to the first item of a C buffer to write into,
  #  `size` the number of bytes it can store, and `py_buffer` a Python byte buffer)
  buffer_ptr = ctypes.cast(buffer_ptr, ctypes.POINTER(ctypes.c_char * size))
  # Read from the Python buffer, starting at its current position, directly into the C buffer
  # (until the target is full or the end of the source is reached)
  n_bytes = py_buffer.readinto(buffer_ptr.contents)  # returns the number of bytes read
  ```

* If you wish to check whether two objects returned by PDFium are the same, the `is` operator won't help because `ctypes` does not have original object return (OOR), i. e. new, equivalent Python objects are created each time, although they might represent one and the same C object.[^ctypes_no_oor]
  That's why you'll want to use `ctypes.addressof()` to get the memory addresses of the underlying C object.
  For instance, this is used to avoid infinite loops on circular bookmark references when iterating through the document outline:
  ```python
  # (Assuming `pdf` is an FPDF_DOCUMENT)
  seen = set()
  bookmark = pdfium_c.FPDFBookmark_GetFirstChild(pdf, None)
  while bookmark:
      # bookmark is a pointer, so we need to use its `contents` attribute to get the object the pointer refers to
      # (otherwise we'd only get the memory address of the pointer itself, which would result in random behaviour)
      address = ctypes.addressof(bookmark.contents)
      if address in seen:
          break  # circular reference detected
      else:
          seen.add(address)
      bookmark = pdfium_c.FPDFBookmark_GetNextSibling(pdf, bookmark)
  ```
  
  [^ctypes_no_oor]: Confer the [ctypes documentation on Pointers](https://docs.python.org/3/library/ctypes.html#pointers).

* In many situations, callback functions come in handy.[^callback_usecases] Thanks to `ctypes`, it is seamlessly possible to use callbacks across Python/C language boundaries.
  
  [^callback_usecases]: e. g. incremental read/write, management of progressive tasks, ...
  
  Example: Loading a document from a Python buffer. This way, file access can be controlled in Python while the whole data does not need to be in memory at once.
  ```python
  import os
  
  # Factory class to create callable objects holding a reference to a Python buffer
  class _reader_class:
    
    def __init__(self, py_buffer):
        self.py_buffer = py_buffer
    
    def __call__(self, _, position, p_buf, size):
        # Write data from Python buffer into C buffer, as explained before
        buffer_ptr = ctypes.cast(p_buf, ctypes.POINTER(ctypes.c_char * size))
        self.py_buffer.seek(position)
        self.py_buffer.readinto(buffer_ptr.contents)
        return 1  # non-zero return code for success
  
  # (Assuming py_buffer is a Python file buffer, e. g. io.BufferedReader)
  # Get the length of the buffer
  py_buffer.seek(0, os.SEEK_END)
  file_len = py_buffer.tell()
  py_buffer.seek(0)
  
  # Set up an interface structure for custom file access
  fileaccess = pdfium_c.FPDF_FILEACCESS()
  fileaccess.m_FileLen = file_len
  
  # Assign the callback, wrapped in its CFUNCTYPE
  fileaccess.m_GetBlock = type(fileaccess.m_GetBlock)( _reader_class(py_buffer) )
  
  # Finally, load the document
  pdf = pdfium_c.FPDF_LoadCustomDocument(fileaccess, None)
  ```

<!-- TODO mention pdfium_i.get_bufreader() as a shortcut to set up an FPDF_FILEACCESS interface -->

* When using the raw API, special care needs to be taken regarding object lifetime, considering that Python may garbage collect objects as soon as their reference count reaches zero. However, the interpreter has no way of magically knowing how long the underlying resources of a Python object might still be needed on the C side, so measures need to be taken to keep such objects referenced until PDFium does not depend on them anymore.
  
  If resources need to remain valid after the time of a function call, PDFium docs usually indicate this clearly. Ignoring requirements on object lifetime will lead to memory corruption (commonly resulting in a segfault).
  
  For instance, the docs on `FPDF_LoadCustomDocument()` state that
  > The application must keep the file resources |pFileAccess| points to valid until the returned FPDF_DOCUMENT is closed. |pFileAccess| itself does not need to outlive the FPDF_DOCUMENT.
  
  This means that the callback function and the Python buffer need to be kept alive as long as the `FPDF_DOCUMENT` is used.
  This can be achieved by referencing these objects in an accompanying class, e. g.
  
  ```python
  class PdfDataHolder:
      
      def __init__(self, buffer, function):
          self.buffer = buffer
          self.function = function
      
      def close(self):
          # Make sure both objects remain available until this function is called
          # No-op id() call to denote that the object needs to stay in memory up to this point
          id(self.function)
          self.buffer.close()
  
  # ... set up an FPDF_FILEACCESS structure
  
  # (Assuming `py_buffer` is the buffer and `fileaccess` the FPDF_FILEACCESS interface)
  data_holder = PdfDataHolder(py_buffer, fileaccess.m_GetBlock)
  pdf = pdfium_c.FPDF_LoadCustomDocument(fileaccess, None)
  
  # ... work with the pdf
  
  # Close the PDF to free resources
  pdfium_c.FPDF_CloseDocument(pdf)
  # Close the data holder, to keep the object itself and thereby the objects it
  # references alive up to this point, as well as to release the buffer
  data_holder.close()
  ```

* Finally, let's finish with an example how to render the first page of a document to a `PIL` image in `RGBA` color format.
  ```python
  import math
  import ctypes
  import os.path
  import PIL.Image
  import pypdfium2.raw as pdfium_c
  
  # Load the document
  filepath = os.path.abspath("tests/resources/render.pdf")
  pdf = pdfium_c.FPDF_LoadDocument((filepath+"\x00").encode("utf-8"), None)
  
  # Check page count to make sure it was loaded correctly
  page_count = pdfium_c.FPDF_GetPageCount(pdf)
  assert page_count >= 1
  
  # Load the first page and get its dimensions
  page = pdfium_c.FPDF_LoadPage(pdf, 0)
  width  = math.ceil(pdfium_c.FPDF_GetPageWidthF(page))
  height = math.ceil(pdfium_c.FPDF_GetPageHeightF(page))
  
  # Create a bitmap
  use_alpha = False  # We don't render with transparent background
  bitmap = pdfium_c.FPDFBitmap_Create(width, height, int(use_alpha))
  # Fill the whole bitmap with a white background
  # The color is given as a 32-bit integer in ARGB format (8 bits per channel)
  pdfium_c.FPDFBitmap_FillRect(bitmap, 0, 0, width, height, 0xFFFFFFFF)
  
  # Store common rendering arguments
  render_args = (
      bitmap,  # the bitmap
      page,    # the page
      # positions and sizes are to be given in pixels and may exceed the bitmap
      0,       # left start position
      0,       # top start position
      width,   # horizontal size
      height,  # vertical size
      0,       # rotation (as constant, not in degrees!)
      pdfium_c.FPDF_LCD_TEXT | pdfium_c.FPDF_ANNOT,  # rendering flags, combined with binary or
  )
  
  # Render the page
  pdfium_c.FPDF_RenderPageBitmap(*render_args)
  
  # Get a pointer to the first item of the buffer
  buffer_ptr = pdfium_c.FPDFBitmap_GetBuffer(bitmap)
  # Re-interpret the pointer to encompass the whole buffer
  buffer_ptr = ctypes.cast(buffer_ptr, ctypes.POINTER(ctypes.c_ubyte * (width * height * 4)))
  
  # Create a PIL image from the buffer contents
  img = PIL.Image.frombuffer("RGBA", (width, height), buffer_ptr.contents, "raw", "BGRA", 0, 1)
  # Save it as file
  img.save("out.png")
  
  # Free resources
  pdfium_c.FPDFBitmap_Destroy(bitmap)
  pdfium_c.FPDF_ClosePage(page)
  pdfium_c.FPDF_CloseDocument(pdf)
  ```

### [Command-line Interface](https://pypdfium2.readthedocs.io/en/stable/shell_api.html)

pypdfium2 also ships with a simple command-line interface, providing access to key features of the support model in a shell environment (e. g. rendering, content extraction, document inspection, page rearranging, ...).

The primary motivation behind this is to have a nice testing interface, but it may be helpful in a variety of other situations as well.
Usage should be largely self-explanatory, assuming a minimum of familiarity with the command-line.


## Licensing

PDFium and pypdfium2 are available by the terms and conditions of either [`Apache-2.0`](LICENSES/Apache-2.0.txt) or [`BSD-3-Clause`](LICENSES/BSD-3-Clause.txt), at your choice.
Various other open-source licenses apply to dependencies bundled with PDFium. Verbatim copies of their respective licenses are contained in the file [`LicenseRef-PdfiumThirdParty.txt`](LICENSES/LicenseRef-PdfiumThirdParty.txt), which also has to be shipped with binary redistributions.
Documentation and examples of pypdfium2 are licensed under [`CC-BY-4.0`](LICENSES/CC-BY-4.0.txt).

pypdfium2 complies with the [reuse standard](https://reuse.software/spec/) by including [SPDX](https://spdx.org/licenses/) headers in source files, and license information for data files in [`.reuse/dep5`](.reuse/dep5).

To the author's knowledge, pypdfium2 is one of the rare Python libraries that are capable of PDF rendering while not being covered by copyleft licenses (such as the `GPL`).[^liberal_pdf_renderlibs]

As of early 2023, a single developer is author and rightsholder of the code base (apart from a few minor [code contributions](https://github.com/pypdfium2-team/pypdfium2/graphs/contributors)).

[^liberal_pdf_renderlibs]: The only other liberal-licensed PDF rendering libraries known to the author are [`pdf.js`](https://github.com/mozilla/pdf.js/) (JavaScript) and [`Apache PDFBox`](https://github.com/apache/pdfbox) (Java), but python bindings packages don't exist yet or are unsatisfactory. However, we wrote some gists that show it'd be possible in principle: [pdfbox](https://gist.github.com/mara004/51c3216a9eabd3dcbc78a86d877a61dc) (+ [setup](https://gist.github.com/mara004/881d0c5a99b8444fd5d1d21a333b70f8)), [pdfjs](https://gist.github.com/mara004/87276da4f8be31c80c38036c6ab667d7).


## Issues

While using pypdfium2, you might encounter bugs or missing features.
In this case, feel free to file an issue. If applicable, include details such as tracebacks, OS and CPU type, as well as the versions of pypdfium2 and used dependencies.

Roadmap:
* pypdfium2
  - [Issues panel](https://github.com/pypdfium2-team/pypdfium2/issues): Initial bug reports and feature requests. May need to be transferred to dependencies.
  - [Discussions page](https://github.com/pypdfium2-team/pypdfium2/discussions): General questions and suggestions.
* PDFium
  - [Bug tracker](https://bugs.chromium.org/p/pdfium/issues/list): Issues in PDFium.
    Beware: The bridge between Python and C increases the probability of integration issues or API misuse. The symptoms can often make it look like a PDFium bug while it is not.
  - [Mailing list](https://groups.google.com/g/pdfium/): Questions regarding PDFium usage.
* [pdfium-binaries](https://github.com/bblanchon/pdfium-binaries/issues): Binary builder.
* [ctypesgen](https://github.com/ctypesgen/ctypesgen/issues): Bindings generator.

### Known limitations

#### Incompatibility with CPython 3.7.6 and 3.8.1

pypdfium2 built with mainstream ctypesgen cannot be used with releases 3.7.6 and 3.8.1 of the CPython interpreter due to a [regression](https://github.com/python/cpython/pull/16799#issuecomment-612353119) that [broke](https://github.com/ctypesgen/ctypesgen/issues/77) ctypesgen-created string handling code.

Since version 4, pypdfium2 is built with a patched fork of ctypesgen that removes ctypesgen's problematic string code.

#### Risk of unknown object lifetime violations

As outlined in the raw API section, it is essential that Python-managed resources remain available as long as they are needed by PDFium.

The problem is that the Python interpreter may garbage collect objects with reference count zero at any time, so an unreferenced but still required object may either by chance stay around long enough or disappear too soon, resulting in non-deterministic memory issues that are hard to debug.
If the timeframe between reaching reference count zero and removal is sufficiently large and roughly consistent across different runs, it is even possible that mistakes regarding object lifetime remain unnoticed for a long time.

Although we intend to develop helpers carefully, it cannot be fully excluded that unknown object lifetime violations are still lurking around somewhere, especially if unexpected requirements were not documented by the time the code was written.

#### Missing raw PDF access

As of this writing, PDFium's public interface does not provide access to the raw PDF data structure (see [issue 1694](https://crbug.com/pdfium/1694)). It does not expose APIs to read/write PDF dictionaries, streams, name/number trees, etc. Instead, it merely offers a predefined set of abstracted functions. This considerably limits the library's potential, compared to other products such as `pikepdf`.

#### Limitations of ABI bindings

PDFium's non-public backend would provide extended capabilities, including [raw access](#missing-raw-pdf-access), but it is not exported into the ABI and written in C++ (not pure C), so we cannot use it with `ctypes`. This means it's out of scope for this project.

Also, while ABI bindings tend to be more convenient, they have some technical drawbacks compared to API bindings (see e.g. [1](https://cffi.readthedocs.io/en/latest/overview.html#abi-versus-api), [2](https://github.com/ocrmypdf/OCRmyPDF/issues/541#issuecomment-1834684532))


## Development
<!-- TODO wheel tags, maintainer access, GitHub peculiarities -->

This section contains some key information relevant for project maintainers.

### Long lines

The pypdfium2 codebase does not hard wrap long lines.
It is recommended to set up automatic word wrap in your text editor, e.g. VS Code:
```
editor.wordWrap = bounded
editor.wordWrapColumn = 100
```

### Docs

pypdfium2 provides API documentation using [Sphinx](https://github.com/sphinx-doc/sphinx/), which can be rendered to various formats, including HTML:
```bash
sphinx-build -b html ./docs/source ./docs/build/html/
./run build  # short alias
```

Built docs are primarily hosted on [`readthedocs.org`](https://readthedocs.org/projects/pypdfium2/).
It may be configured using a [`.readthedocs.yaml`](.readthedocs.yaml) file (see [instructions](https://docs.readthedocs.io/en/stable/config-file/v2.html)), and the administration page on the web interface.
RTD supports hosting multiple versions, so we currently have one linked to the `main` branch and another to `stable`.
New builds are automatically triggered by a webhook whenever you push to a linked branch.

Additionally, one doc build can also be hosted on [GitHub Pages](https://pypdfium2-team.github.io/pypdfium2/index.html).
It is implemented with a CI workflow, which is supposed to be triggered automatically on release.
This provides us with full control over the build env and the used commands, whereas RTD may be less liberal in this regard.


### Testing

pypdfium2 contains a small test suite to verify the library's functionality. It is written with [pytest](https://github.com/pytest-dev/pytest/):
```bash
./run test
```

Note that ...
* you can pass `-sv` to get more detailed output.
* `$DEBUG_AUTOCLOSE=1` may be set to get debugging information on automatic object finalization.

To get code coverage statistics, you may call
```bash
./run coverage
```

Sometimes, it can also be helpful to test code on many PDFs.[^testing_corpora]
In this case, the command-line interface and `find` come in handy:
```bash
# Example A: Analyse PDF images (in the current working directory)
find . -name '*.pdf' -exec bash -c "echo \"{}\" && pypdfium2 pageobjects \"{}\" --filter image" \;
# Example B: Parse PDF table of contents
find . -name '*.pdf' -exec bash -c "echo \"{}\" && pypdfium2 toc \"{}\"" \;
```

[^testing_corpora]: For instance, one could use the testing corpora of open-source PDF libraries (pdfium, pikepdf/ocrmypdf, mupdf/ghostscript, tika/pdfbox, pdfjs, ...)

### Release workflow

The release process is fully automated using Python scripts and scheduled release workflows.
You may also trigger the workflow manually using the GitHub Actions panel or the [`gh`](https://cli.github.com/) command-line tool.

Python release scripts are located in the folder `setupsrc/pypdfium2_setup`, along with custom setup code:
* `update_pdfium.py` downloads binaries.
* `craft_packages.py pypi` builds platform-specific wheel packages and a source distribution suitable for PyPI upload.
* `autorelease.py` takes care of versioning, changelog, release note generation and VCS checkin.

The autorelease script has some peculiarities maintainers should know about:
* The changelog for the next release shall be written into `docs/devel/changelog_staging.md`.
  On release, it will be moved into the main changelog under `docs/source/changelog.md`, annotated with the PDFium version update.
  It will also be shown on the GitHub release page.
* pypdfium2 versioning uses the pattern `major.minor.patch`, optionally with an appended beta mark (e. g. `2.7.1`, `2.11.0`, `3.0.0b1`, ...).
  Version changes are based on the following logic:
  * If PDFium was updated, the minor version is incremented.
  * If only pypdfium2 code was updated, the patch version is incremented instead.
  * Major updates and beta marks are controlled via `autorelease/config.json`.
    If `major` is true, the major version is incremented.
    If `beta` is true, a new beta tag is set, or an existing one is incremented.
    The control file is automatically reset when the versioning is finished.
  * If switching from a beta release to a non-beta release, only the beta mark is removed while minor and patch versions remain unchanged.

In case of necessity, you may also forego autorelease/CI and do the release manually, which will roughly work like this (though ideally it should never be needed):
* Commit changes to the version file
  ```bash
  git add src/pypdfium2/version.py
  git commit -m "increment version"
  git push
  ```
* Create a new tag that matches the version file
  ```bash
  # substitute $VERSION accordingly
  git tag -a $VERSION
  git push --tags
  ```
* Build the packages
  ```bash
  python setupsrc/pypdfium2_setup/update_pdfium.py
  python setupsrc/pypdfium2_setup/craft_packages.py pypi
  ```
* Upload to PyPI
  ```bash
  # make sure the packages are valid
  twine check dist/*
  # upload to PyPI (this will interactively ask for your username/password)
  twine upload dist/*
  ```
* Update the `stable` branch to trigger a documentation rebuild
  ```bash
  git checkout stable
  git rebase origin/main  # alternatively: git reset --hard main
  git checkout main
  ```

If something went wrong with commit or tag, you can still revert the changes:
```bash
# perform an interactive rebase to change history (substitute $N_COMMITS with the number of commits to drop or modify)
git rebase -i HEAD~$N_COMMITS
git push --force
# delete local tag (substitute $TAGNAME accordingly)
git tag -d $TAGNAME
# delete remote tag
git push --delete origin $TAGNAME
```
Faulty PyPI releases may be yanked using the web interface.


## Thanks to[^thanks_to]

<!-- order: alphabetical by surname -->

* [Benoît Blanchon](https://github.com/bblanchon): Author of [PDFium binaries](https://github.com/bblanchon/pdfium-binaries/) and [patches](sourcebuild/patches/).
* [Anderson Bravalheri](https://github.com/abravalheri): Help with PEP 517/518 compliance. Hint to use an environment variable rather than separate setup files.
* [Bastian Germann](https://github.com/bgermann): Help with inclusion of licenses for third-party components of PDFium.
* [Tim Head](https://github.com/betatim): Original idea for Python bindings to PDFium with ctypesgen in `wowpng`.
* [Yinlin Hu](https://github.com/YinlinHu): `pypdfium` prototype and `kuafu` PDF viewer.
* [Adam Huganir](https://github.com/adam-huganir): Help with maintenance and development decisions since the beginning of the project.
* [kobaltcore](https://github.com/kobaltcore): Bug fix for `PdfDocument.save()`.
* [Mike Kroutikov](https://github.com/mkroutikov): Examples on how to use PDFium with ctypes in `redstork` and `pdfbrain`.
* [Peter Saalbrink](https://github.com/petersaalbrink): Code style improvements to the multipage renderer.

... and further [code contributors](https://github.com/pypdfium2-team/pypdfium2/graphs/contributors) (GitHub stats).

*If you have somehow contributed to this project but we forgot to mention you here, please let us know.*

[^thanks_to]: People listed in this section may not necessarily have contributed any copyrightable code to the repository. Some have rather helped with ideas, or contributions to dependencies of pypdfium2.


## History

### PDFium

The PDFium code base was originally developed as part of the commercial Foxit SDK, before being acquired and open-sourced by Google, who maintain PDFium independently ever since, while Foxit continue to develop their SDK closed-source.

### pypdfium2

pypdfium2 is the successor of *pypdfium* and *pypdfium-reboot*.

Inspired by *wowpng*, the first known proof of concept Python binding to PDFium using ctypesgen, the initial *pypdfium* package was created. It had to be updated manually, which did not happen frequently. There were no platform-specific wheels, but only a single wheel that contained binaries for 64-bit Linux, Windows and macOS.

*pypdfium-reboot* then added a script to automate binary deployment and bindings generation to simplify regular updates. However, it was still not platform specific.

pypdfium2 is a full rewrite of *pypdfium-reboot* to build platform-specific wheels and consolidate the setup scripts. Further additions include ...
* A CI workflow to automatically release new wheels every Tuesday
* Support models that conveniently wrap the raw PDFium/ctypes API
* Test code
* A script to build PDFium from source
