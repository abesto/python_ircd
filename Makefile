.PHONY: setup unittest integration-test test listen mypy all black pylint

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
	./run_integration_tests.sh

mypy:
	pipenv run mypy . --ignore-missing-imports

test: mypy unittest integration-test

listen:
	pipenv run python ./application.py
