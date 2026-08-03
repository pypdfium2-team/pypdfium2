# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Pyodide support helpers

import os
import shlex

# local
from base import log, env_prepend, run_cmd
from _build_helpers import Compiler


def _prepend_each(value, iterable):
    for item in iterable:
        yield value
        yield item

def info(compiler):
    log(
        "Warning: pyodide support is experimental. The resulting builds are known to be flaky and susceptible to various types of occasional, random crashes. Use with caution!\n"
        "HELP WANTED: If you are in a position to track down and fix these issues, please reach out. Thanks!"
    )
    if compiler is not None:
        log("CAUTION: With --pyodide, using a non-default compiler config is not recommended.")

def configure(config, compiler):
    config.update({
        "target_os": "emscripten",
        "target_cpu": "wasm",
        "pdf_is_complete_lib": True,
        "emscripten_path": os.environ["PYODIDE_EMSCRIPTEN_DIR"],
    })
    # Note: There's also `pyodide config list` and `pyodide config get $key`, but for some reason this does not work within a running `pyodide build` session. Thus get flags from the (undocumented) build-time variables below.
    # See also https://pyodide-build.readthedocs.io/en/latest/how-to/compiler-flags.html and https://pyodide-build.readthedocs.io/en/latest/how-to/debugging.html#check-active-configuration
    for flags_group in ("C", "CXX", "LD"):
        flags_var = flags_group + "FLAGS"
        env_prepend(flags_var, os.environ[f"SIDE_MODULE_{flags_var}"], " ")
    env_prepend("CPPFLAGS", "-Wno-unknown-warning-option -Wno-deprecated-pragma", " ")
    # use the default //build/toolchain/wasm/BUILD.gn toolchain even if base mode is gcc
    # (comment this out if you want to use our plain gcc toolchain)
    if compiler is Compiler.clang:
        config["use_sized_deallocation"] = True
    elif compiler is Compiler.gcc:
        del config["custom_toolchain"], config["host_toolchain"]
    else:
        assert False, compiler

def link(build_dir):
    libpdfium_a = build_dir/"obj"/"libpdfium.a"
    libpdfium_so = build_dir/"libpdfium.so"
    # Is this all right? Not sure, but it seems to work.
    # See also https://emscripten.org/docs/tools_reference/emcc.html#arguments and https://emscripten.org/docs/tools_reference/settings_reference.html
    ldflags = shlex.split(os.environ["LDFLAGS"])
    em_cmd = ["em++", str(libpdfium_a), "-shared", *ldflags, "-o", str(libpdfium_so)]
    s_opts = dict(EXPORT_ALL=1, ALLOW_MEMORY_GROWTH=1, ALLOW_TABLE_GROWTH=1)
    em_cmd += _prepend_each("-s", (f"{k}={v}" for k, v in s_opts.items()))
    run_cmd(em_cmd, cwd=build_dir)
