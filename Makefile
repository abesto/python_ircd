.PHONY: setup unittest integration-test test listen mypy

all: test

setup:
	pipenv --three --dev

unittest:
	pipenv run nosetests tests

integration-test:
	./run_integration_tests.sh

mypy:
	pipenv run mypy . --ignore-missing-imports

test: mypy unittest integration-test

listen:
	pipenv run python ./application.py

