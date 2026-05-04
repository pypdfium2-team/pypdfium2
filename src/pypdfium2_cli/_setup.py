# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import logging
import warnings
import functools
from collections import defaultdict
import pypdfium2_cfg


def _get_loglevel(envvar, default):
    return getattr(logging, os.environ.get(envvar, default).upper())

def setup_logging():
    
    # could also pass through the log level by parameter, but using an env var seemed easiest for now
    loglevel = _get_loglevel("PYPDFIUM_LOGLEVEL", "debug")
    loggers = [logging.getLogger("pypdfium2"+m) for m in ("", "_raw", "_cfg", "_cli")]
    streamhandler = logging.StreamHandler()
    for l in loggers:
        l.addHandler(streamhandler)
        l.setLevel(loglevel)
    
    warnings.simplefilter("always")
    
    # cli_logger = logging.getLogger("pypdfium2_cli")
    # cli_logger.debug("Just set up logging")
    
    debug_unsupported = bool(int( os.environ.get("DEBUG_UNSUPPORTED", 1) ))
    debug_sysfonts = bool(int( os.environ.get("DEBUG_SYSFONTS", 0) ))
    pypdfium2_cfg.DEBUG_AUTOCLOSE.value = _get_loglevel("DEBUG_AUTOCLOSE", "warning")
    
    import pypdfium2._helpers as pdfium
    from pypdfium2_cli._sysfonts import PdfSysfontListener
    if debug_unsupported:
        pdfium.PdfUnspHandler().setup()
    if debug_sysfonts:
        PdfSysfontListener().setup()


if sys.version_info < (3, 8):  # pragma: no cover
    def cached_property(func):
        return property( functools.lru_cache(maxsize=1)(func) )
else:
    cached_property = functools.cached_property

# could even inherit just from dict if we changed __init__ to take the factory
class keydefaultdict (defaultdict):
    def __missing__(self, key):
        value = self.default_factory(key)
        self[key] = value
        return value
