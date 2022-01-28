# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import argparse
from typing import (
    Callable,
    Sequence,
)


HelpFlags = ('help', '--help', '-h', '/h', '?', '/?')
VersionFlags = ('version', '--version', '-v')


class ArgParser (argparse.ArgumentParser):
    
    # Cutsomised argument parser
    
    def __init__(self, *args, **kws):
        super().__init__(*args, **kws)

    def parse_args(self, argv=None, namespace=None):
        
        if argv is None:
            argv = sys.argv[1:]
        
        if len(argv) < 1 or (argv[0].lower() in HelpFlags):
            self.print_help(sys.stderr)
            sys.exit()
        
        return super().parse_args(argv, namespace)


class _SubcommandItem:
    
    def __init__(
            self,
            name: str,
            method: Callable,
            help: str = "",
        ):
        self.name = name
        self.method = method
        self.help = help


class CliRunner:
    
    def __init__(
            self,
            program: str,
            version: str,
            description: str,
            argv: Sequence[str] = sys.argv,
        ):
        self.program = program
        self.version = version
        self.description = description
        self.argv = argv
        self._subs = []
    
    
    def add_subcommand(self, *args, **kws):
        self._subs.append( _SubcommandItem(*args, **kws) )
    
    
    def _get_help(self) -> str:
        
        help = ""
        
        # header: program name, version, and description
        help += "{} {}".format(self.program, self.version) + '\n'
        help += self.description + '\n'*2
        
        sep = ''
        for sub in self._subs:
            help += sep + sub.name + '\n'
            help += ' '*4 + sub.help
            sep = '\n'
        
        return help
    
    
    def run(self):

        if len(self.argv) < 1 or self.argv[0] in HelpFlags:
            print(self._get_help())
            sys.exit()
        
        main_arg = self.argv[0]
        
        if main_arg in VersionFlags:
            print( "{} {}".format(self.program, self.version) )
            sys.exit()
        
        sc_found = False
        
        for sub in self._subs:
            if main_arg.lower() == sub.name.lower():
                sc_found = True
                sub.method(
                    argv = self.argv[1:],
                    prog = "pypdfium2 {}".format(sub.name),
                    desc = sub.help,
                )
        
        if not sc_found:
            print("Error: Argument '{}' is not a valid subcommand".format(main_arg), file=sys.stderr)
