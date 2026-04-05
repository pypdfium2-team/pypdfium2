# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import logging
import warnings
import pypdfium2_cfg


def setup_logging():
        
    # could also pass through the log level by parameter, but using an env var seemed easiest for now
    loglevel = getattr(logging, os.environ.get("PYPDFIUM_LOGLEVEL", "debug").upper())
    loggers = [logging.getLogger("pypdfium2"+m) for m in ("", "_raw", "_cfg", "_cli")]
    for l in loggers:
        l.addHandler(logging.StreamHandler())
        l.setLevel(loglevel)
    
    warnings.simplefilter("always")
    logging.captureWarnings(True)
    
    # cli_logger = logging.getLogger("pypdfium2_cli")
    # cli_logger.debug("Just set up logging")
    
    debug_autoclose = bool(int( os.environ.get("DEBUG_AUTOCLOSE", 0) ))
    debug_unsupported = bool(int( os.environ.get("DEBUG_UNSUPPORTED", 1) ))
    debug_sysfonts = os.environ.get("DEBUG_SYSFONTS", "")
    pypdfium2_cfg.DEBUG_AUTOCLOSE.value = debug_autoclose
    
    import pypdfium2._helpers as pdfium
    from pypdfium2_cli._aux import PdfSysfontListener
    if debug_unsupported:
        pdfium.PdfUnspHandler().setup()
    if debug_sysfonts:
        PdfSysfontListener().setup()
