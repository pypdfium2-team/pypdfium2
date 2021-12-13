# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import logging


def setup_logger(logger):
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter()
    
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
