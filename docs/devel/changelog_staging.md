<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Finally implemented automatic closing of objects by implementing `__del__` finaliser methods,
  while taking into account the requirement that an object may not be closed if a superordinate object has been closed already.
  It is still recommended that you call `close()` manually, to release memory independent of Python garbage collection.
  However, the risk of memory leaks is now greatly reduced.
