<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- This release fixes compatibility with Python 3.7 and 3.6.
  * Runtime support was inadvertently broken due to a faulty cached property backport which held only one cache per class, not per instance as should have been.
    The accidental loss of caches broke key assumptions of our autoclose logic, which relies on `cached_property` since 5.8.0. (Earlier versions that did not make extensive use of cached properties should work in essentials, but have not been explicitly tested.)
  * This release replaces both `functools.cached_property` and the faulty `functools.lru_cache()` based backport with our own, backward compatible `cached_property` implementation along with thorough documentation.
  * Also, fixed setup (i.e. source installation) with Python 3.6 and its max available setup dependency versions (that is, `setuptools` 59).
    - This had probably been broken for a long time. (A few non-breaking issues remain, e.g. for some reason we end up with a `purelib` directory, but it should be `platlib`. If you know how to fix this, please reach out.)
    - Made gn-dist's setup Python 3.6 compatible likewise. Wheels should have been compatible already.
    - Note that ctypesgen continues to require Python `>=3.8` at this time (3.6 compatibility is not a priority here), but you can install with `--no-build-isolation` and let the reference bindings be used, or try adding ctypesgen's `src/` to `PYTHONPATH` to bypass setup, and see how it goes.
  * Maintainer's note: Python 3.6 was a very decent version of Python – the first to have f-strings and insertion order preserving dictionaries –, and has been supported by stable distributions like SUSE, RHEL and Ubuntu for a long time, so it is still worth restoring support.
- `gn-dist` improvements. Changed versioning and release process so that CI no longer needs to push to the repository. More documentation added. manylinux2014 compatibility and build instructions.
- With `container_driver.py`, added ability to test source installation, and to select another container image. This can be used to test pypdfium2 in a manylinux2014 container with Python 3.6.
- TODO document CI changes, MANIFEST.in fix, PEP 735 dependency groups etc., experimental pyemscrpiten builds
