# SPDX-FileCopyrightText: 2021 Adam Huganir <adam@huganir.com>
# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0

test:
	python3 -m pytest tests/ tests_old/

coverage:
	python3 -m coverage run --omit "tests/*,tests_old/*,src/pypdfium2/raw.py,setupsrc/*" -m pytest tests/ tests_old/
	python3 -m coverage report

docs-build:
	python3 -m sphinx -b html ./docs/source ./docs/build/html

docs-open:
	xdg-open ./docs/build/html/index.html

update-all:
	python3 ./setupsrc/pl_setup/update_pdfium.py

setup-all:
	python3 ./setupsrc/pl_setup/craft_wheels.py

check:
	bash ./utilities/check.sh

clean:
	bash ./utilities/clean.sh

packaging:
	bash ./utilities/packaging.sh
