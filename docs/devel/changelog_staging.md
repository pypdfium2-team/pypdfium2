<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `render_to()` was fixed to actually allow callables. The code passage in question was unreachable due to an unguarded `issubclass()` check before.
