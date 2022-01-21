#! /usr/bin/env python3

import os
import subprocess


problematic = ("pathlib", 'f"', "f'")

def main():
    for string in problematic:
        command = [
            "grep",
            "-r",
            string,
            "--include",
            "*.py",
            "--exclude-dir",
            "sourcebuild",
            "--exclude-dir",
            "data",
        ]
        print(command)
        subprocess.run(command, cwd=os.getcwd())
        print()


if __name__ == '__main__':
    main()
