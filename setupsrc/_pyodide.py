# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Pyodide support helpers

import os
import shlex

# local
from base import log, env_prepend, run_cmd
from _build_helpers import Compiler


# Documentation reference:
# https://pyodide.org/en/latest/development/abi.html
# https://pyodide-build.readthedocs.io/en/latest/how-to/compiler-flags.html
# https://pyodide-build.readthedocs.io/en/latest/how-to/debugging.html#check-active-configuration
# https://emscripten.org/docs/compiling/Dynamic-Linking.html
# https://emscripten.org/docs/tools_reference/emcc.html#arguments
# https://emscripten.org/docs/tools_reference/settings_reference.html
# https://emscripten.org/docs/optimizing/Optimizing-Code.html#how-to-optimize-code


def info(compiler):
    log(
        "Warning: pyodide support is experimental. The resulting builds are known to be flaky and susceptible to various types of occasional, random crashes. Use with caution!\n"
        "HELP WANTED: If you are in a position to track down and fix these issues, please reach out. Thanks!"
    )
    if compiler is not None:
        log("CAUTION: With --pyodide, using a non-default compiler config is not recommended.")


def configure(config, compiler):
    config.update({
        "is_debug": True,  # XXX
        "target_os": "emscripten",
        "target_cpu": "wasm",
        "pdf_is_complete_lib": True,
        "emscripten_path": os.environ["PYODIDE_EMSCRIPTEN_DIR"],
    })
    env_prepend("CFLAGS", f"{os.environ['CFLAGS_BASE']} -I{os.environ['PYTHONINCLUDE']} -O2 -g", " ")
    env_prepend("CXXFLAGS", f"{os.environ['CFLAGS_BASE']} -O2 -g", " ")
    env_prepend("LDFLAGS", f"{os.environ['LDFLAGS_BASE']} -sSIDE_MODULE=1 -O2 -g", " ")
    env_prepend("CPPFLAGS", "-Wno-unknown-warning-option -Wno-deprecated-pragma", " ")
    if compiler is Compiler.clang:
        config["use_sized_deallocation"] = True
    elif compiler is Compiler.gcc:
        # use the default //build/toolchain/wasm/BUILD.gn toolchain even if base mode is gcc
        # (comment this out if you want to use our plain gcc toolchain)
        del config["custom_toolchain"], config["host_toolchain"]
    else:
        assert False, compiler


def link(build_dir):
    # FIXME Is this all right? Not sure. Linkage itself works, but there are runtime issues.
    libpdfium_a = build_dir/"obj"/"libpdfium.a"
    libpdfium_so = build_dir/"libpdfium.so"
    ldflags = shlex.split(os.environ["LDFLAGS"])
    em_cmd = ["em++", str(libpdfium_a), "-shared", *ldflags, "-o", str(libpdfium_so)]
    # em_cmd += ["-sALLOW_MEMORY_GROWTH=1", "-sALLOW_TABLE_GROWTH=1"]
    run_cmd(em_cmd, cwd=build_dir)
