<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- This release fixes compatibility with Python 3.7 and 3.6.
  * Runtime support was inadvertently broken due to a faulty cached property backport which held only one cache per class, not per instance as should have been.
  * The accidental loss of caches broke key assumptions of our autoclose logic, which relies on `cached_property` since 5.8.0. (Earlier versions that did not make extensive use of `cached_property` should work in essentials, but have not been explicitly tested.)
  * This release replaces both `functools.cached_property` and the faulty `functools.lru_cache()` based backport with our own, backward compatible `cached_property` implementation along with thorough documentation.
  * Also, fixed setup (i.e. source installation) with Python 3.6 and its max available setup dependency versions (that is, `setuptools` 59). This had probably been broken for a long time. (A few non-breaking issues remain, e.g. for some reason we end up with a `purelib` directory, but it should be `platlib`. If you know how to fix this, please reach out.)
  * Maintainer's note: Python 3.6 is (or was) a very decent version of Python – the first to have f-strings and insertion order preserving dictionaries –, and has (or had) been supported by stable distributions like SUSE, RHEL and Ubuntu for a long time.
- With `container_driver.py`, added ability to test source installation, and to select another container image. This can be used to test pypdfium2 in a manylinux2014 container with Python 3.6.
- TODO document CI changes, MANIFEST.in fix, etc.
