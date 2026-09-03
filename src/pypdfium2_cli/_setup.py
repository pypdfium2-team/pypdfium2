# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import logging
import warnings


_LogLevelMap = {
    'debug':    logging.DEBUG,
    'info':     logging.INFO,
    'warning':  logging.WARNING,
    'error':    logging.ERROR,
    'critical': logging.CRITICAL,
}

_DebugAutocloseMap = {
    -1: logging.CRITICAL,
    0: logging.WARNING,
    1: logging.DEBUG,
}

def _readbool(string):
    return bool(int(string))

def _do_cast(cast, value, exc_type, choices=None):
    try:
        return cast(value)
    except exc_type as e:
        if choices:
            raise ValueError(f"{value!r} not in {tuple(choices)}") from e
        else:
            raise ValueError(f"{value!r} cannot be casted via {cast.__name__}") from e

def _env(key, default, cast=None, map=None):
    value = os.environ.get(key)
    if value is None:
        return default
    if cast:
        value = _do_cast(cast, value, ValueError)
    if map:
        value = _do_cast(map.__getitem__, value, KeyError, choices=map)
    return value


def setup_logging():
    
    # Read these settings from environment variables
    # (Could also consider using CLI flags, but this seemed easiest for now ...)
    loglevel          = _env("PYPDFIUM_LOGLEVEL", logging.DEBUG, cast=str.lower, map=_LogLevelMap)
    debug_autoclose   = _env("DEBUG_AUTOCLOSE",   logging.WARNING, cast=int, map=_DebugAutocloseMap)
    debug_unsupported = _env("DEBUG_UNSUPPORTED", 1, cast=_readbool)
    debug_sysfonts    = _env("DEBUG_SYSFONTS",    0, cast=_readbool)
    
    loggers = [logging.getLogger("pypdfium2"+m) for m in ("", "_raw", "_cfg", "_cli")]
    streamhandler = logging.StreamHandler()
    for l in loggers:
        l.addHandler(streamhandler)
        l.setLevel(loglevel)
    warnings.simplefilter("always")
    # cli_logger = logging.getLogger("pypdfium2_cli")
    # cli_logger.debug("Just set up logging")
    
    import pypdfium2_cfg
    pypdfium2_cfg.DEBUG_AUTOCLOSE.value = debug_autoclose
    
    import pypdfium2._helpers as pdfium
    from pypdfium2_cli._sysfonts import PdfSysfontListener
    if debug_unsupported:
        pdfium.PdfUnspHandler().setup()
    if debug_sysfonts:
        PdfSysfontListener().setup()
