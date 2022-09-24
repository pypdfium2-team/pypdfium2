<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Finally implemented automatic closing of objects by implementing `__del__` finaliser methods, taking into account that Python may call finalisers in an arbitrary order while objects must not be closed if one of their parents is closed already. It is still recommended that you call `close()` manually, to release memory independent of Python garbage collection. However, the risk of memory leaks due to missing `close()` calls is now greatly reduced.
