# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys
import argparse
from typing import (
    Callable,
    Sequence,
    Union,
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
            names: Union[str, Sequence[str]],
            method: Callable,
            help: str = "",
        ):
        if isinstance(names, str):
            self.names = (names, )
        else:
            self.names = names
        self.method = method
        self.help = help


class CliParser:
    
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
    
    
    @staticmethod
    def _get_cmd_help(flags, message) -> str:
        
        help = ''
        
        sep = ''
        for flag in flags:
            help += sep + flag
            sep = ', '
        
        if len(flags) > 1:
            help = '({})'.format(help)
        
        help += '\n' + ' '*4 + message
        
        return help
    
    
    def _get_main_help(self) -> str:
        
        help = ''
        
        help += '{} {}'.format(self.program, self.version) + '\n'
        help += self.description + '\n'*2
        
        help += self._get_cmd_help(
            HelpFlags, "Show the main help an exit",
        ) + '\n'
        help += self._get_cmd_help(
            VersionFlags, "Show the versions of bindings and library",
        ) + '\n'
        
        sep = ''
        for sub in self._subs:
            help += sep + self._get_cmd_help(sub.names, sub.help)
            sep = '\n'
        
        return help
    
    
    def run(self):

        if len(self.argv) < 1 or self.argv[0] in HelpFlags:
            print(self._get_main_help())
            sys.exit()
        
        main_arg = self.argv[0]
        
        if main_arg in VersionFlags:
            print( "{} {}".format(self.program, self.version) )
            sys.exit()
        
        sc_found = False
        
        for sub in self._subs:
            if main_arg.lower() in [n.lower() for n in sub.names]:
                sc_found = True
                sub.method(
                    argv = self.argv[1:],
                    prog = "{} {}".format(self.program, main_arg),
                    desc = sub.help,
                )
        
        if not sc_found:
            print("Error: Argument '{}' is not a valid subcommand".format(main_arg), file=sys.stderr)
