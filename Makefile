# SPDX-FileCopyrightText: 2021 Adam Huganir <adam@huganir.com>
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0

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

packaging:
	bash ./utilities/packaging.sh

.PHONY: build
build:
	bash ./utilities/build.sh

clean:
	bash ./utilities/clean.sh

docs-build:
	sphinx-build ./docs/source ./docs/build/html

docs-open:
	xdg-open ./docs/build/html/index.html
