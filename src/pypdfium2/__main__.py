# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import os.path
import warnings
from pypdfium2_cli.__main__ import *

_DEPRECATION_REASON = " Using a separate submodule is necessary to allow for proper preparation before library init (e.g. set up logging), since a module's __main__.py implies its __init__.py."

if __name__ == "__main__":
    _py_exe = os.path.basename(sys.executable)
    warnings.simplefilter("always")
    warnings.warn(f"`{_py_exe} -m pypdfium2` is deprecated. Use `{_py_exe} -m pypdfium2_cli` or the `pypdfium2` entrypoint script instead."+_DEPRECATION_REASON, category=DeprecationWarning, stacklevel=2)
    cli_main()
else:
    warnings.warn("Importing pypdfium2.__main__ is deprecated. Use pypdfium2_cli.__main__ instead."+_DEPRECATION_REASON, category=DeprecationWarning, stacklevel=2)
