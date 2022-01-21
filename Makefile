# SPDX-FileCopyrightText: 2021 Adam Huganir <adam@huganir.com>
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0 

release:
	bash ./utilities/release.sh

update-all:
	python3 update.py

setup-all:
	bash ./utilities/setup_all.sh

build:
	python3 build_pdfium.py
	python3 setup_source.py bdist_wheel

clean:
	bash ./utilities/clean.sh

compcheck:
	python3 ./utilities/compcheck.py
