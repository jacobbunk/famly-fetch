
VENV?=${VIRTUAL_ENV}

${VENV}/bin/activate:
	python3.13 -m venv ${VENV}

venv: ${VENV}/bin/activate

install: pyproject.toml venv
	${VENV}/bin/pip3 install -e .[dev]

format:
	${VENV}/bin/ruff format

ruff-check:
	${VENV}/bin/ruff check

package:
	${VENV}/bin/python -m build

test-publish:
	${VENV}/bin/python -m twine upload --repository testpypi dist/*

publish:
	${VENV}/bin/python -m twine upload --repository pypi dist/*
