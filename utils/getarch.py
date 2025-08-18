# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Simple uname shim for cibuildwheel, with ability to add "-unknown" suffix to platforms that need it.
# Note that handling this as bash expression in config is problematic, as a failed if-check would propagate an errcode, causing the scriptlet to terminate. It seems that cibuildwheel does not use `bash -e`, and that's only a dirty workaround anyway. Error handling is a fundamental issue with shell langauges.

import subprocess

proc = subprocess.run(["uname", "-m"], stdout=subprocess.PIPE)
value = proc.stdout.decode().strip()
if value == "loongarch64":
    value += "-unknown"

print(value)
