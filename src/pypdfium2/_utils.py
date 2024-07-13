# SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import importlib.util


def deferred_import(modpath):
    
    # FIXME If modpath points to a submodule, the parent module will be loaded immediately when this function is called. This is a limitation of the find_spec() importlib API used here. However, this may still be useful if the parent is a mere namespace package that does not contain anything expensive, as in the case of PIL.
    
    module = sys.modules.get(modpath, None)
    if module is not None:
        return module  # shortcut
    
    # assuming an optional dependency
    # returning None will simply let it fail with an AttributeError when attempting to access the module
    try:
        spec = importlib.util.find_spec(modpath)
    except ModuleNotFoundError:
        return None
    if spec is None:
        return None
    
    # see https://docs.python.org/3/library/importlib.html#implementing-lazy-imports
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[modpath] = module
    loader.exec_module(module)
    
    return module
