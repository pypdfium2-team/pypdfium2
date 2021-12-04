# SPDX-FileCopyrightText: 2021 Adam Huganir <adam@huganir.com>
# SPDX-License-Identifier: CC-BY-4.0 

release: clean update-binaries build-all
		check-wheel-contents dist/*

build-all: build-darwin-arm64 build-darwin-x64 build-linux-arm32 build-linux-arm64 \
		build-win-x64 build-win-x86 build-linux-x64

build-darwin-x64:
	python3 setup_darwin_x64.py   bdist_wheel

build-darwin-arm64:
	python3 setup_darwin_arm64.py bdist_wheel

build-linux-x64:
	python3 setup_linux_x64.py    bdist_wheel

build-linux-arm64:
	python3 setup_linux_arm64.py  bdist_wheel

build-linux-arm32:
	python3 setup_linux_arm32.py  bdist_wheel

build-win-x64:
	python3 setup_windows_x64.py  bdist_wheel

build-win-x86:
	python3 setup_windows_x86.py  bdist_wheel

update-binaries:
	python3 update.py

clean:
	bash clean.sh
