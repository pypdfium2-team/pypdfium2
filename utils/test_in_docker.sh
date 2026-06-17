# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

eval "$PREPARE_CMD"
# alternatively: python3 -m pip config set global.break-system-packages true
python3 -m venv --system-site-packages testenv
VENV_PY=/testenv/bin/python3

cd /pypdfium2
CPUNAME=$(uname -m)
if [ "$CPUNAME" == "mips64" ]; then
    # pip refuses the wheel, no matter if we're using "mips64" (matching uname), "mips64le" or whatever. This quick & dirty hack lets us install the wheel anyway.
    SITE_PACKAGES="/testenv/lib/python3.11/site-packages"
    $VENV_PY -m pip install --platform manylinux_2_17_mips64 --no-deps --target "$SITE_PACKAGES" ./wheelhouse/*.whl
else
    $VENV_PY -m pip install ./wheelhouse/*.whl
fi
$VENV_PY -m pytest tests/
