# SPDX-FileCopyrightText: 2021 Adam Huganir <adam@huganir.com>
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0 

build:
	python3 build.py
	python3 setup_source.py bdist_wheel

release:
	bash release.sh

update-all:
	python3 update.py

setup-all:
	bash setup_all.sh

clean:
	bash clean.sh

setup-darwin-x64:
	python3 update.py -p darwin-x64
	python3 setup_darwin_x64.py   bdist_wheel

setup-darwin-arm64:
	python3 update.py -p darwin-arm64
	python3 setup_darwin_arm64.py bdist_wheel

setup-linux-x64:
	python3 update.py -p linux-x64
	python3 setup_linux_x64.py    bdist_wheel

setup-linux-arm64:
	python3 update.py -p linux-arm64
	python3 setup_linux_arm64.py  bdist_wheel

setup-linux-arm32:
	python3 update.py -p linux-arm32
	python3 setup_linux_arm32.py  bdist_wheel

setup-windows-x64:
	python3 update.py -p windows-x64
	python3 setup_windows_x64.py  bdist_wheel

setup-windows-x86:
	python3 update.py -p windows-x86
	python3 setup_windows_x86.py  bdist_wheel
