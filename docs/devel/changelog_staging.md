<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Changelog for next release

- Wheels are now correctly flagged as impure, for they contain a binary extension.
- Merged `trigger.yaml` into `release.yaml` workflow, and `autorelease.py` into `mk_releasenotes.py`, which significantly simplifies the code base.
- Changed autorelease schedule from 12 to 10 o'clock UTC.
