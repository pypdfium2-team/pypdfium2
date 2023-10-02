<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# PR 263 (versioning improvements)

## pre-merge
- Properly integrate version data source (git/supply/fallback) and editable info. Maybe we should also add an `uncertain` attribute based on this info?
  * What is the cleanest way of embedding this into the version file?
  * How should we add this to the version str? We'd need some separator other than dot to keep it parsable, but it seems like PEP 440 doesn't allow. Do we have to forego PEP 440 in the library, and exclude the info from PyPA tools?

## post-merge
- Fix polluted integration of sourcebuild version (see comments in `version.py`).
- Change autorelease to swap minor/patch versioning logic. In terms of API, the helpers version is probably more significant than the pdfium version.
- Consider including auto-generated third-party license file from pdfium binaries.
- Progress `sys` target to build/include bindings for a given version. Integrate version file. Allow managing through `run emplace`.
- Extract only the binaries in question, not whole archives. Download headers from pdfium directly. Build bindings only once and share in a `data/` cache.
- Include binary/bindings hashes in the pdfium version file. For performance reasons, we should not validate this on init, but rather provide the caller with a validate function.
- Think about how we will handle versioning/tagging with the future Conda packages. We'll probably need new tag formats for the two conda packages, e.g. `conda_{raw,helpers}/$PYPI_TAG-$BUILD`.
- Consider a git pull hook to auto-update helpers version file of editable install.
