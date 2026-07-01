#! /usr/bin/env python3

import sys

delimiter = sys.argv[1]  # use e.g. $'\n' in bash
args = sys.argv[2:]
print(delimiter.join(args))
