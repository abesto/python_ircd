.PHONY: setup unittest integration-test test listen mypy all black pylint update

all: black test

setup:
	pipenv install --dev

black:
	pipenv run black .

pylint:
	pipenv run pylint *.py $(shell ls */__init__.py  | cut -f1 -d/)

unittest:
	pipenv run nosetests tests

integration-test:
	pipenv run nosetests integration_tests.py

mypy:
	pipenv run mypy . --ignore-missing-imports

test: mypy unittest integration-test

listen:
	pipenv run python ./application.py

update:
	pipenv update --pre  # The --pre is needed because of `black`
