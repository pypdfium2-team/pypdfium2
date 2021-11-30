# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

V_MAJOR = 0
V_MINOR = 1
V_PATCH = 0
V_BETA  = 0

V_PYPDFIUM2 = "{}.{}.{}".format(V_MAJOR, V_MINOR, V_PATCH)
if V_BETA is not None:
    V_PYPDFIUM2 += "b{}".format(V_BETA)

V_LIBPDFIUM = 4678
