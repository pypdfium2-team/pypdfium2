# SPDX-FileCopyrightText: 2021 Adam Huganir <adam@huganir.com>
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0

test:
	python3 -m pytest ./tests/

check:
	bash ./utilities/check.sh

update-all:
	python3 ./setupsrc/pl_setup/update_pdfium.py

setup-all:
	python3 ./setupsrc/pl_setup/craft_wheels.py

packaging:
	bash ./utilities/packaging.sh

clean:
	bash ./utilities/clean.sh

docs-build:
	sphinx-build -b html ./docs/source ./docs/build/html

docs-open:
	xdg-open ./docs/build/html/index.html
