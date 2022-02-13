# SPDX-FileCopyrightText: 2021 Adam Huganir <adam@huganir.com>
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0

install:
	bash utilities/install.sh

test:
	python3 -m pytest tests/

release:
	bash ./utilities/release.sh

update-all:
	python3 platform_setup/update_pdfium.py

setup-all:
	bash ./utilities/setup_all.sh

build:
	python3 platform_setup/build_pdfium.py
	python3 platform_setup/setup_source.py bdist_wheel

clean:
	bash ./utilities/clean.sh

render-docs:
	sphinx-build ./docs/source ./docs/build/html

open-docs:
	xdg-open ./docs/build/html/index.html
