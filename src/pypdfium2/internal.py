# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# while `internal` is already part of the helpers namespace, the purpose of
# this wrapper file is that the caller can do `import pypdfium2.internal as ...`

from pypdfium2._helpers._internal import *
