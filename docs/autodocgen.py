#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

V_AUTODOCGEN = '0.0.1'

Preable = """\
.. SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
.. SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

.. This file was automatically generated using Autodocgen {}

"""


import argparse
import importlib


def main(
        module_name,
        exclude_libs,
        exclude_members,
        exclude_prefices,
        exclude_suffices,
        title,
        output_file,
    ):
    
    excs = []
    excs += exclude_members
    for lib in exclude_libs:
        excs += dir(importlib.import_module(lib))
    
    content = Preable.format(V_AUTODOCGEN)
    content += title + '\n' + '='*len(title) + '\n'*2
    
    module = importlib.import_module(module_name)
    members = dir(module)
    
    for member_str in members:
        
        if any(member_str.startswith(p) for p in exclude_prefices):
            continue
        if any(member_str.endswith(s) for s in exclude_suffices):
            continue
        if member_str.endswith('_') and member_str[:-1] in members:
            continue
        if member_str in excs:
            continue
        
        member = getattr(module, member_str)
        member_path = "{}.{}".format(module_name, member_str)
        
        if callable(member):
            content += ".. autofunction:: {}".format(member_path)
        else:
            content += ".. data:: {}\n    :value: {}".format(member_path, member)
        
        content += '\n'
    
    with open(output_file, 'w') as fh:
        fh.write(content)


def parse_args():
    parser = argparse.ArgumentParser(
        description = "Auto-generate a Sphinx documentation file for bindings created by ctypesgen.",
    )
    parser.add_argument(
        '--module-name',
        help = "Module path as it would be imported",
        default = "pypdfium2._pypdfium",
    )
    parser.add_argument(
        '--exclude-libs',
        nargs = '*',
        help = "Libraries to exclude that are imported using a wildcard in the module to document.",
        default = ['ctypes'],
    )
    parser.add_argument(
        '--exclude-members',
        nargs = '*',
        default = ['sys', 'ctypes', 're', 'os', 'glob', 'platform'],
        help = "Full names of members to exclude",
    )
    parser.add_argument(
        '--exclude-prefices',
        nargs = '*',
        default = ['_', 'struct_', 'enum_'],
        help = "Prefices of members to exclude",
    )
    parser.add_argument(
        '--exclude-suffices',
        nargs = '*',
        default = ['_t__'],
        help = "Suffices of members to exclude",
    )
    parser.add_argument(
        '--title',
        default = "PDFium API",
        help = "Title for the output file",
    )
    parser.add_argument(
        '--output-file',
        help = "Path to the output file",
        default = "./source/pdfium_api.rst",
    )
    return parser.parse_args()


def run_main():
    args = parse_args()
    main(
        module_name = args.module_name,
        exclude_libs = args.exclude_libs,
        exclude_members = args.exclude_members,
        exclude_prefices = args.exclude_prefices,
        exclude_suffices = args.exclude_suffices,
        title = args.title,
        output_file = args.output_file,
    )


if __name__ == '__main__':
    run_main()
