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

release:
	bash ./utilities/release.sh

build:
	python3 platform_setup/build_pdfium.py --check-deps
	PYP_TARGET_PLATFORM="sourcebuild" python3 -m build -n -x --wheel
	PYP_TARGET_PLATFORM="sourcebuild" python3 -m pip install . -v --no-build-isolation
	printf "InitialState" > platform_setup/setup_status.txt

clean:
	bash ./utilities/clean.sh

render-docs:
	sphinx-build ./docs/source ./docs/build/html

open-docs:
	xdg-open ./docs/build/html/index.html
