# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import logging


def setup_logger(logger):
    handler = logging.StreamHandler()
    logger.addHandler(handler)
