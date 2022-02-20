# SPDX-FileCopyrightText: 2021 Adam Huganir <adam@huganir.com>
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0

# Tell make that all our targets are not associated with files
.PHONY: install test check update-all setup-all release build clean docs-build docs-open

install:
	bash ./utilities/install.sh

test:
	python3 -m pytest tests/

check:
	bash ./utilities/check.sh

update-all:
	python3 platform_setup/update_pdfium.py

setup-all:
	bash ./utilities/setup_all.sh

release:
	bash ./utilities/release.sh

build:
	bash ./utilities/build.sh

clean:
	bash ./utilities/clean.sh

docs-build:
	sphinx-build ./docs/source ./docs/build/html

docs-open:
	xdg-open ./docs/build/html/index.html
