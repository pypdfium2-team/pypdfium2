# SPDX-FileCopyrightText: 2021 Adam Huganir <adam@huganir.com>
# SPDX-License-Identifier: CC-BY-4.0 

release:
	bash release.sh

update:
	python3 update.py

build:
	python3 build.py
	python3 setup_source.py bdist_wheel

clean:
	bash clean.sh

setup-all:
	bash setup_all.sh

setup-darwin-x64:
	python3 setup_darwin_x64.py   bdist_wheel

setup-darwin-arm64:
	python3 setup_darwin_arm64.py bdist_wheel

setup-linux-x64:
	python3 setup_linux_x64.py    bdist_wheel

setup-linux-arm64:
	python3 setup_linux_arm64.py  bdist_wheel

setup-linux-arm32:
	python3 setup_linux_arm32.py  bdist_wheel

setup-win-x64:
	python3 setup_windows_x64.py  bdist_wheel

setup-win-x86:
	python3 setup_windows_x86.py  bdist_wheel
